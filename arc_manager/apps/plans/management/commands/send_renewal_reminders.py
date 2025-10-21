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
    help = 'Envía UN recordatorio de renovación a organizaciones cuya suscripción vence en las próximas 24-48 horas'

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
            
            # Buscar suscripciones que vencen en las próximas 24-48 horas
            # Ventana amplia para cubrir todas las zonas horarias y asegurar que nadie se quede sin aviso
            start_window = now + timedelta(hours=24)  # Desde mañana a esta hora
            end_window = now + timedelta(hours=48)    # Hasta pasado mañana a esta hora
            
            subs_expiring_soon = Subscription.objects.filter(
                end_date__gte=start_window,  # Vence después de las próximas 24 horas
                end_date__lte=end_window,    # Vence antes de las próximas 48 horas
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            total_subs = subs_expiring_soon.count()
            
            if total_subs == 0:
                logger.info("No hay suscripciones que venzan en las próximas 24-48 horas")
                self.stdout.write(self.style.SUCCESS('No hay suscripciones que venzan en las próximas 24-48 horas'))
                return
            
            logger.info(f"Encontradas {total_subs} suscripciones que vencen en las próximas 24-48 horas")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] Se enviarían emails a {total_subs} organizaciones'))
            
            sent_count = 0
            failed_count = 0
            skipped_count = 0
            
            site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
            site_url = getattr(settings, 'SITE_URL', 'https://arcmanager.up.railway.app')

            for sub in subs_due_today:
                org = sub.organization
                
                # TEMPORAL: Protección anti-spam desactivada para pruebas
                # Para reactivar, descomenta las siguientes líneas:
                # expiry_date = sub.end_date.strftime('%Y-%m-%d')
                # org_cache_key = f'renewal_reminder_{org.id}_{expiry_date}'
                # if not force and cache.get(org_cache_key):
                #     logger.info(f"Ya se envió recordatorio para vencimiento {expiry_date} a: {org.name}")
                #     skipped_count += 1
                #     continue
                
                expiry_date = sub.end_date.strftime('%Y-%m-%d')
                org_cache_key = f'renewal_reminder_{org.id}_{expiry_date}'
                
                user_email = getattr(org, 'owner_email', None) or getattr(org, 'contact_email', None)
                
                if not user_email:
                    logger.warning(f"Organización sin email: {org.name} (ID: {org.id})")
                    skipped_count += 1
                    continue
                
                # Calcular días restantes para mensaje personalizado
                days_left = (sub.end_date - now).days
                
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Email a: {user_email} - Org: {org.name} - Vence en {days_left} día(s)")
                        sent_count += 1
                        continue
                    
                    # Mensaje dinámico según el tiempo restante
                    if days_left <= 1:
                        subject = f'¡Tu suscripción vence mañana! - {site_name}'
                    else:
                        subject = f'Tu suscripción vence en {days_left} días - {site_name}'
                    
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
                    
                    # TEMPORAL: Protección anti-spam desactivada para pruebas
                    # Para reactivar, descomenta la siguiente línea:
                    # cache.set(org_cache_key, True, timeout=604800)  # 7 días
                    
                    logger.info(f"Email enviado exitosamente a: {user_email} - Org: {org.name}")
                    sent_count += 1
                    
                except Exception as email_error:
                    # Si falla un email, continuar con los demás
                    logger.error(
                        f"Error enviando email a {user_email} (Org: {org.name}): {email_error}",
                        exc_info=True
                    )
                    failed_count += 1
            
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


