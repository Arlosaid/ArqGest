from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import timedelta
import logging

from apps.plans.models import Subscription
from core.email_utils import send_resend_email


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía recordatorios de renovación (T-0) a organizaciones con suscripción que vence hoy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar envío ignorando protección de duplicados',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular ejecución sin enviar emails reales',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        try:
            now = timezone.now()
            today_key = now.strftime('%Y-%m-%d')
            cache_key = f'renewal_reminders_sent_{today_key}'
            
            # Protección contra ejecuciones duplicadas el mismo día
            if not force and cache.get(cache_key):
                logger.info(f"Recordatorios ya enviados hoy ({today_key}). Usa --force para forzar.")
                self.stdout.write(self.style.WARNING(f'Ya se enviaron recordatorios hoy ({today_key})'))
                return
            
            # Solo vencen hoy (T-0)
            start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_today = start_today + timedelta(days=1)
            subs_due_today = Subscription.objects.filter(
                end_date__gte=start_today,
                end_date__lt=end_today,
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            total_subs = subs_due_today.count()
            
            if total_subs == 0:
                logger.info("No hay suscripciones que venzan hoy")
                self.stdout.write(self.style.SUCCESS('No hay suscripciones que venzan hoy'))
                return
            
            logger.info(f"Encontradas {total_subs} suscripciones que vencen hoy")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] Se enviarían {total_subs} emails'))
            
            sent_count = 0
            failed_count = 0
            skipped_count = 0
            
            site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
            site_url = getattr(settings, 'SITE_URL', 'https://arcmanager.up.railway.app')

            for sub in subs_due_today:
                org = sub.organization
                user_email = getattr(org, 'owner_email', None) or getattr(org, 'contact_email', None)
                
                if not user_email:
                    logger.warning(f"Organización sin email: {org.name} (ID: {org.id})")
                    skipped_count += 1
                    continue
                
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Email a: {user_email} - Org: {org.name}")
                        sent_count += 1
                        continue
                    
                    subject = f'¡URGENTE! Tu suscripción vence hoy - {site_name}'
                    
                    # Renderizar template
                    context = {
                        'site_name': site_name,
                        'protocol': 'https',
                        'domain': site_url.replace('https://', '').replace('http://', ''),
                        'organization_name': org.name,
                        'plan_name': sub.plan.display_name,
                        'renewal_url': f'{site_url}/plans/subscription/',
                    }
                    
                    html = render_to_string('emails/renewal_reminder_email.html', context)
                    send_resend_email(user_email, subject, html)
                    
                    logger.info(f"Email enviado exitosamente a: {user_email} - Org: {org.name}")
                    sent_count += 1
                    
                except Exception as email_error:
                    # Si falla un email, continuar con los demás
                    logger.error(
                        f"Error enviando email a {user_email} (Org: {org.name}): {email_error}",
                        exc_info=True
                    )
                    failed_count += 1

            # Marcar como ejecutado hoy (válido por 24 horas)
            if not dry_run:
                cache.set(cache_key, True, timeout=86400)
            
            # Resumen
            summary = (
                f"Enviados: {sent_count} | "
                f"Fallidos: {failed_count} | "
                f"Sin email: {skipped_count} | "
                f"Total: {total_subs}"
            )
            
            logger.info(f"Resumen de envío - {summary}")
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {summary}'))
            elif failed_count > 0:
                self.stdout.write(self.style.WARNING(summary))
            else:
                self.stdout.write(self.style.SUCCESS(summary))

        except Exception as e:
            logger.error(f"Error crítico en send_renewal_reminders: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'Error crítico: {str(e)}'))
            raise  # Re-lanzar para que cron lo detecte como fallo


