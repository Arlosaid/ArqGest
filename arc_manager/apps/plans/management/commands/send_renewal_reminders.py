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
            
            # Buscar suscripciones que vencen en las próximas 48 horas (incluye hoy y mañana)
            # Ventana amplia para cubrir todas las zonas horarias y asegurar que nadie se quede sin aviso
            end_window = now + timedelta(hours=48)    # Hasta pasado mañana a esta hora
            
            subs_expiring_soon = Subscription.objects.filter(
                end_date__gte=now,          # Vence desde ahora en adelante
                end_date__lte=end_window,   # Vence antes de las próximas 48 horas
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            total_subs = subs_expiring_soon.count()
            
            if total_subs == 0:
                logger.info("No hay suscripciones que venzan en las próximas 48 horas")
                self.stdout.write(self.style.SUCCESS('No hay suscripciones que venzan en las próximas 48 horas'))
                return
            
            logger.info(f"Encontradas {total_subs} suscripciones que vencen en las próximas 48 horas")
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] Se enviarían emails a {total_subs} organizaciones'))
            
            # Log detallado de suscripciones encontradas
            for sub in subs_expiring_soon:
                days_left = (sub.end_date - now).days
                logger.info(f"Suscripción encontrada: {sub.organization.name} - Plan: {sub.plan.display_name} - Vence en {days_left} días - Fecha: {sub.end_date}")
            
            sent_count = 0
            failed_count = 0
            skipped_count = 0
            
            site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
            site_url = getattr(settings, 'SITE_URL', 'https://arcmanager.up.railway.app')

            for sub in subs_expiring_soon:
                org = sub.organization
                
                # Protección anti-spam inteligente: evitar enviar múltiples emails para el mismo vencimiento
                expiry_date = sub.end_date.strftime('%Y-%m-%d')
                org_cache_key = f'renewal_reminder_{org.id}_{expiry_date}'
                
                cache_value = cache.get(org_cache_key)
                logger.info(f"Verificando cache para {org.name}: clave={org_cache_key}, valor={cache_value}, force={force}")
                
                if not force and cache_value:
                    logger.info(f"Ya se envió recordatorio para vencimiento {expiry_date} a: {org.name} (cache hit)")
                    skipped_count += 1
                    continue
                
                # Obtener TODOS los administradores de la organización
                try:
                    org_admins = org.users.filter(is_org_admin=True)
                    if org_admins.exists():
                        admin_emails = [admin.email for admin in org_admins]
                        logger.info(f"Administradores encontrados para {org.name}: {admin_emails}")
                    else:
                        # Si no hay admin, usar el primer usuario de la organización
                        first_user = org.users.first()
                        admin_emails = [first_user.email] if first_user else []
                        logger.info(f"No hay admins, usando primer usuario para {org.name}: {admin_emails}")
                except Exception as e:
                    logger.error(f"Error obteniendo emails para organización {org.name}: {e}")
                    admin_emails = []
                
                if not admin_emails:
                    logger.warning(f"Organización sin usuarios con email: {org.name} (ID: {org.id})")
                    skipped_count += 1
                    continue
                
                # Calcular días restantes para mensaje personalizado
                days_left = (sub.end_date - now).days
                
                # Enviar email a TODOS los administradores
                for user_email in admin_emails:
                    try:
                        logger.info(f"Procesando email para: {user_email} - Org: {org.name} - Vence en {days_left} día(s)")
                        
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
                        
                        logger.info(f"Renderizando template para {user_email} con contexto: {context}")
                        html = render_to_string('emails/renewal_reminder_email.html', context)
                        logger.info(f"Template renderizado exitosamente para {user_email}, longitud HTML: {len(html)} caracteres")
                        
                        logger.info(f"Enviando email a {user_email} con asunto: {subject}")
                        result = send_resend_email(user_email, subject, html)
                        logger.info(f"Resultado de send_resend_email para {user_email}: {result}")
                        
                        # Verificar si el email se envió realmente
                        if result and result.get('id'):
                            # Marcar como enviado para este vencimiento específico (válido por 7 días)
                            # Esto evita enviar múltiples emails para el mismo vencimiento
                            cache.set(org_cache_key, True, timeout=604800)  # 7 días
                            logger.info(f"Cache marcado como enviado para {org.name}: {org_cache_key}")
                            
                            logger.info(f"Email enviado exitosamente a: {user_email} - Org: {org.name} - ID: {result.get('id')}")
                            sent_count += 1
                        else:
                            # Si no se pudo enviar, no marcar como enviado y contar como fallido
                            logger.error(f"Error: send_resend_email retornó resultado inválido para {user_email} - Org: {org.name} - Resultado: {result}")
                            failed_count += 1
                        
                        # Pequeño delay para evitar rate limiting de Resend (2 req/seg)
                        time.sleep(0.6)  # 600ms entre emails
                        
                    except Exception as email_error:
                        # Si falla un email, continuar con los demás
                        logger.error(
                            f"Error enviando email a {user_email} (Org: {org.name}): {email_error}",
                            exc_info=True
                        )
                        failed_count += 1
            
            # Resumen detallado
            summary = (
                f"Enviados: {sent_count} | "
                f"Fallidos: {failed_count} | "
                f"Sin email: {skipped_count} | "
                f"Total: {total_subs}"
            )
            
            logger.info(f"Resumen de envío - {summary}")
            logger.info(f"Detalles: {sent_count} emails enviados exitosamente, {failed_count} fallaron, {skipped_count} omitidos")
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] {summary}'))
            elif failed_count > 0:
                self.stdout.write(self.style.WARNING(f'⚠️  {summary} - Revisar logs para detalles de errores'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✅ {summary} - Todos los emails enviados exitosamente'))

        except Exception as e:
            logger.error(f"Error crítico en send_renewal_reminders: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'Error crítico: {str(e)}'))
            raise  # Re-lanzar para que cron lo detecte como fallo


