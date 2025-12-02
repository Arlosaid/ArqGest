from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import timedelta
import logging
import time

from apps.plans.models import Subscription, UpgradeRequest, Plan


logger = logging.getLogger('plans.notifications')


class Command(BaseCommand):
    help = 'Envía notificación por email a organizaciones cuyo trial expiró HOY (día 0)'

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
        from core.email_utils import send_resend_email
        
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        try:
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Buscar trials que expiraron HOY (end_date está entre inicio y fin del día)
            # O trials que tienen status trial_expired y end_date fue hoy
            expired_trials = Subscription.objects.filter(
                subscription_status='trial_expired',
                end_date__gte=today_start,
                end_date__lt=today_end
            ).select_related('organization', 'plan')
            
            total_subs = expired_trials.count()
            
            if total_subs == 0:
                self.stdout.write('No hay trials expirados hoy')
                return
            
            logger.debug(f"Trials expirados hoy: {total_subs}")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {total_subs} organizaciones con trial expirado'))
            
            sent_count = 0
            failed_count = 0
            skipped_count = 0
            
            site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
            site_url = getattr(settings, 'SITE_URL', 'https://arcmanager.up.railway.app')
            
            # Obtener info del plan básico para el email
            basic_plan = Plan.get_basic_plan()
            basic_plan_info = {
                'name': basic_plan.display_name if basic_plan else 'Plan Básico',
                'price': str(basic_plan.price) if basic_plan else 'N/A',
                'max_users': basic_plan.max_users if basic_plan else 'N/A',
                'max_storage_gb': basic_plan.max_storage_gb if basic_plan else 'N/A',
                'billing_cycle_days': basic_plan.billing_cycle_days if basic_plan else 30,
            }

            for sub in expired_trials:
                org = sub.organization
                expiry_date = sub.end_date.strftime('%Y-%m-%d')
                org_cache_key = f'trial_expiration_notice_{org.id}_{expiry_date}'
                
                # Verificar cache para evitar duplicados
                if not force and cache.get(org_cache_key):
                    skipped_count += 1
                    continue
                
                # Verificar si hay UpgradeRequest pendiente
                has_pending_upgrade = UpgradeRequest.objects.filter(
                    organization=org,
                    status='pending'
                ).exists()
                
                if has_pending_upgrade:
                    logger.debug(f"Omitido: {org.name} tiene upgrade pendiente")
                    skipped_count += 1
                    continue
                
                # Obtener SOLO administradores de la organización
                org_admins = org.users.filter(is_org_admin=True)
                admin_emails = [admin.email for admin in org_admins]
                
                if not admin_emails:
                    logger.warning(f"Sin admins: {org.name}")
                    skipped_count += 1
                    continue
                
                emails_sent_for_org = 0
                
                # Enviar email a todos los administradores
                for user_email in admin_emails:
                    try:
                        if dry_run:
                            self.stdout.write(f"  [DRY RUN] Enviaría a: {user_email} ({org.name})")
                            sent_count += 1
                            emails_sent_for_org += 1
                            continue
                        
                        subject = f'Tu prueba gratuita ha terminado - {site_name}'
                        
                        context = {
                            'site_name': site_name,
                            'protocol': 'https',
                            'domain': site_url.replace('https://', '').replace('http://', ''),
                            'organization_name': org.name,
                            'trial_end_date': sub.end_date,
                            'upgrade_url': f'{site_url}/plans/upgrade/',
                            'basic_plan': basic_plan_info,
                        }
                        
                        html = render_to_string('emails/trial_expired_email.html', context)
                        result = send_resend_email(user_email, subject, html)
                        
                        if result and result.get('id'):
                            logger.debug(f"Email enviado: {user_email} - {org.name}")
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
                    cache.set(org_cache_key, True, timeout=604800)  # 7 días
            
            summary = f"Enviados: {sent_count} | Fallidos: {failed_count} | Omitidos: {skipped_count}"
            
            # Solo loguear si hubo actividad relevante
            if sent_count > 0 or failed_count > 0:
                logger.info(f"Trial expiration notices: {summary}")
            
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
