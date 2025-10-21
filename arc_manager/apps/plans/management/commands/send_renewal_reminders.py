from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import timedelta
import logging
import time

from apps.plans.models import Subscription
from core.email_utils import send_resend_email


logger = logging.getLogger('plans.reminders')


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
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Limpiar cache de recordatorios antes de ejecutar',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        clear_cache = options.get('clear_cache', False)
        
        try:
            now = timezone.now()
            
            if clear_cache:
                try:
                    cache_keys = [k for k in cache.keys('renewal_reminder_*') if k]
                    if cache_keys:
                        cache.delete_many(cache_keys)
                        logger.info(f"Cache limpiado: {len(cache_keys)} entradas")
                except Exception:
                    logger.warning("No se pudo limpiar cache (método no soportado)")
            
            end_window = now + timedelta(hours=48)
            
            subs_expiring_soon = Subscription.objects.filter(
                end_date__gte=now,
                end_date__lte=end_window,
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            total_subs = subs_expiring_soon.count()
            
            if total_subs == 0:
                self.stdout.write('No hay suscripciones por vencer')
                return
            
            logger.info(f"Suscripciones encontradas: {total_subs}")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {total_subs} emails por enviar'))
            
            sent_count = 0
            failed_count = 0
            skipped_count = 0
            
            site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
            site_url = getattr(settings, 'SITE_URL', 'https://arcmanager.up.railway.app')

            for sub in subs_expiring_soon:
                org = sub.organization
                expiry_date = sub.end_date.strftime('%Y-%m-%d')
                org_cache_key = f'renewal_reminder_{org.id}_{expiry_date}'
                
                # Verificar cache para evitar duplicados
                if not force and cache.get(org_cache_key):
                    skipped_count += 1
                    continue
                
                # Obtener administradores de la organización
                org_admins = org.users.filter(is_org_admin=True)
                admin_emails = [admin.email for admin in org_admins] if org_admins.exists() else []
                
                if not admin_emails:
                    first_user = org.users.first()
                    admin_emails = [first_user.email] if first_user else []
                
                if not admin_emails:
                    logger.warning(f"Sin emails: {org.name}")
                    skipped_count += 1
                    continue
                
                days_left = (sub.end_date - now).days
                emails_sent_for_org = 0
                
                # Enviar email a todos los administradores
                for user_email in admin_emails:
                    try:
                        if dry_run:
                            sent_count += 1
                            emails_sent_for_org += 1
                            continue
                        
                        subject = f'¡Tu suscripción vence mañana! - {site_name}' if days_left <= 1 else f'Tu suscripción vence en {days_left} días - {site_name}'
                        
                        context = {
                            'site_name': site_name,
                            'protocol': 'https',
                            'domain': site_url.replace('https://', '').replace('http://', ''),
                            'organization_name': org.name,
                            'plan_name': sub.plan.display_name,
                            'renewal_url': f'{site_url}/plans/subscription/',
                            'days_left': days_left,
                            'is_urgent': days_left <= 1,
                        }
                        
                        html = render_to_string('emails/renewal_reminder_email.html', context)
                        result = send_resend_email(user_email, subject, html)
                        
                        if result and result.get('id'):
                            logger.info(f"Email enviado: {user_email} - {org.name}")
                            sent_count += 1
                            emails_sent_for_org += 1
                        else:
                            logger.error(f"Error enviando: {user_email}")
                            failed_count += 1
                        
                        time.sleep(0.6)
                        
                    except Exception as e:
                        logger.error(f"Error {user_email}: {str(e)}")
                        failed_count += 1
                
                # Marcar en cache solo si se envió al menos un email
                if emails_sent_for_org > 0:
                    cache.set(org_cache_key, True, timeout=604800)
            
            summary = f"Enviados: {sent_count} | Fallidos: {failed_count} | Omitidos: {skipped_count}"
            logger.info(f"Resumen: {summary}")
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {summary}'))
            elif failed_count > 0:
                self.stdout.write(self.style.WARNING(f'{summary}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'{summary}'))

        except Exception as e:
            logger.error(f"Error crítico: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise


