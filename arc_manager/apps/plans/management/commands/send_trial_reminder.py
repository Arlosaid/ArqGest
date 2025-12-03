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
    help = 'Envía recordatorio a organizaciones cuyo trial vence en X días (por defecto 1 día)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Días antes de expiración para enviar recordatorio (default: 1)',
        )
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
        
        days_before = options.get('days', 1)
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        try:
            now = timezone.now()
            
            # Buscar trials que vencen en EXACTAMENTE X días
            target_date_start = (now + timedelta(days=days_before)).replace(hour=0, minute=0, second=0, microsecond=0)
            target_date_end = target_date_start + timedelta(days=1)
            
            trials_expiring = Subscription.objects.filter(
                end_date__gte=target_date_start,
                end_date__lt=target_date_end,
                subscription_status='trial_active'
            ).select_related('organization', 'plan')
            
            total_subs = trials_expiring.count()
            
            if total_subs == 0:
                self.stdout.write(f'No hay trials por vencer en {days_before} día(s)')
                return
            
            logger.debug(f"Trials por vencer en {days_before} día(s): {total_subs}")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {total_subs} organizaciones con trial por vencer'))
            
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

            for sub in trials_expiring:
                org = sub.organization
                expiry_date = sub.end_date.strftime('%Y-%m-%d')
                org_cache_key = f'trial_reminder_{days_before}d_{org.id}_{expiry_date}'
                
                # Verificar cache para evitar duplicados
                if not force and cache.get(org_cache_key):
                    skipped_count += 1
                    if dry_run:
                        self.stdout.write(f"  [SKIP] Ya notificado: {org.name}")
                    continue
                
                # Verificar si hay UpgradeRequest pendiente
                has_pending_upgrade = UpgradeRequest.objects.filter(
                    organization=org,
                    status='pending'
                ).exists()
                
                if has_pending_upgrade:
                    logger.debug(f"Omitido: {org.name} tiene upgrade pendiente")
                    skipped_count += 1
                    if dry_run:
                        self.stdout.write(f"  [SKIP] Upgrade pendiente: {org.name}")
                    continue
                
                # Obtener el primer administrador de la organización
                org_admin = org.users.filter(is_org_admin=True).first()
                
                if not org_admin:
                    logger.warning(f"Sin admins: {org.name}")
                    skipped_count += 1
                    continue
                
                user_email = org_admin.email
                
                # Enviar UN solo email por organización
                try:
                    if dry_run:
                        self.stdout.write(f"  [DRY RUN] Enviaría a: {user_email} ({org.name}) - Vence: {sub.end_date.strftime('%d/%m/%Y')}")
                        sent_count += 1
                        continue
                    
                    if days_before == 1:
                        subject = f'Tu prueba gratuita vence mañana - {site_name}'
                    elif days_before == 0:
                        subject = f'Tu prueba gratuita vence hoy - {site_name}'
                    else:
                        subject = f'Tu prueba gratuita vence en {days_before} días - {site_name}'
                    
                    context = {
                        'site_name': site_name,
                        'protocol': 'https',
                        'domain': site_url.replace('https://', '').replace('http://', ''),
                        'organization_name': org.name,
                        'trial_end_date': sub.end_date,
                        'days_remaining': days_before,
                        'upgrade_url': f'{site_url}/plans/solicitar-actualizacion/',
                        'basic_plan': basic_plan_info,
                        'is_urgent': days_before <= 1,
                    }
                    
                    html = render_to_string('emails/trial_reminder_email.html', context)
                    result = send_resend_email(user_email, subject, html)
                    
                    if result and result.get('id'):
                        logger.info(f"Email trial enviado: {user_email} - {org.name}")
                        sent_count += 1
                        # Marcar en cache para evitar duplicados
                        cache.set(org_cache_key, True, timeout=604800)  # 7 días
                    else:
                        logger.error(f"Error enviando: {user_email}")
                        failed_count += 1
                    
                    time.sleep(0.6)
                    
                except Exception as e:
                    logger.error(f"Error {user_email}: {str(e)}")
                    failed_count += 1
            
            summary = f"Enviados: {sent_count} | Fallidos: {failed_count} | Omitidos: {skipped_count}"
            
            # Solo loguear si hubo actividad relevante
            if sent_count > 0 or failed_count > 0:
                logger.info(f"Trial reminders ({days_before}d): {summary}")
            
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
