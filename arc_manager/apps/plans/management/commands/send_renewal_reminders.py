from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import timedelta
import logging
import time

from apps.plans.models import Subscription, RenewalRequest
from core.email_utils import send_resend_email


logger = logging.getLogger('plans.reminders')


class Command(BaseCommand):
    help = 'Envía recordatorio de renovación a organizaciones con plan básico que vence en exactamente 3 días'

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
                        logger.debug(f"Cache limpiado: {len(cache_keys)} entradas")
                except Exception:
                    logger.warning("No se pudo limpiar cache (método no soportado)")
            
            # Buscar suscripciones que vencen en EXACTAMENTE 3 días
            # Solo plan básico activo (no trial)
            target_date_start = (now + timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)
            target_date_end = target_date_start + timedelta(days=1)
            
            subs_expiring_in_3_days = Subscription.objects.filter(
                end_date__gte=target_date_start,
                end_date__lt=target_date_end,
                subscription_status='basic_active'  # Solo plan básico, no trial
            ).select_related('organization', 'plan')

            total_subs = subs_expiring_in_3_days.count()
            
            if total_subs == 0:
                self.stdout.write('No hay suscripciones básicas por vencer en 3 días')
                return
            
            logger.debug(f"Suscripciones encontradas: {total_subs}")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {total_subs} organizaciones con plan por vencer'))
            
            sent_count = 0
            failed_count = 0
            skipped_count = 0
            
            site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
            site_url = getattr(settings, 'SITE_URL', 'https://arcmanager.up.railway.app')

            for sub in subs_expiring_in_3_days:
                org = sub.organization
                expiry_date = sub.end_date.strftime('%Y-%m-%d')
                org_cache_key = f'renewal_reminder_{org.id}_{expiry_date}'
                
                # Verificar cache para evitar duplicados
                if not force and cache.get(org_cache_key):
                    skipped_count += 1
                    continue
                
                # Verificar si hay RenewalRequest pendiente
                has_pending_renewal = RenewalRequest.objects.filter(
                    organization=org,
                    status='pending'
                ).exists()
                
                if has_pending_renewal:
                    logger.debug(f"Omitido: {org.name} tiene renovación pendiente")
                    skipped_count += 1
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
                        self.stdout.write(f"  [DRY RUN] Enviaría a: {user_email} ({org.name})")
                        sent_count += 1
                        continue
                    
                    subject = f'Tu plan vence en 3 días - {site_name}'
                    
                    context = {
                        'site_name': site_name,
                        'protocol': 'https',
                        'domain': site_url.replace('https://', '').replace('http://', ''),
                        'organization_name': org.name,
                        'plan_name': sub.plan.display_name,
                        'renewal_url': f'{site_url}/plans/dashboard/',
                        'days_left': 3,
                        'is_urgent': False,
                    }
                    
                    html = render_to_string('emails/renewal_reminder_email.html', context)
                    result = send_resend_email(user_email, subject, html)
                    
                    if result and result.get('id'):
                        logger.info(f"Email renovación enviado: {user_email} - {org.name}")
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
                logger.info(f"Renewal reminders: {summary}")
            
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


