from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from apps.plans.models import Subscription
from core.email_utils import send_resend_email


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía recordatorios de renovación (T-0) a organizaciones con suscripción que vence hoy'

    def handle(self, *args, **options):
        try:
            now = timezone.now()

            # Solo vencen hoy (T-0)
            start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_today = start_today + timedelta(days=1)
            subs_due_today = Subscription.objects.filter(
                end_date__gte=start_today,
                end_date__lt=end_today,
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            sent_count = 0

            for sub in subs_due_today:
                org = sub.organization
                user_email = getattr(org, 'owner_email', None) or getattr(org, 'contact_email', None)
                if not user_email:
                    continue

                subject = f'¡URGENTE! Tu suscripción vence hoy - {getattr(settings, "SITE_NAME", "ArqGest")}'
                site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
                html = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>¡URGENTE! Suscripción vence hoy - {site_name}</title>
                    <style>
                        @media only screen and (max-width: 600px) {{
                            .email-container {{ width: 100% !important; max-width: 100% !important; }}
                            .email-content {{ padding: 15px !important; }}
                            .email-header {{ padding: 20px !important; }}
                            .email-footer {{ padding: 15px !important; }}
                            .button-container {{ width: 100% !important; }}
                            .button-link {{ display: block !important; width: 100% !important; text-align: center !important; }}
                        }}
                    </style>
                </head>
                <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: Arial, sans-serif;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f5f5f5;">
                        <tr>
                            <td style="padding: 20px;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" class="email-container" style="margin: 0 auto; max-width: 600px; background-color: #ffffff;">
                                    
                                    <!-- Header -->
                                    <tr>
                                        <td class="email-header" style="background-color: #c0392b; padding: 30px; text-align: center;">
                                            <h1 style="margin: 0; font-size: 24px; font-weight: normal; color: #ffffff;">¡URGENTE! Vence Hoy</h1>
                                        </td>
                                    </tr>

                                    <!-- Contenido Principal -->
                                    <tr>
                                        <td class="email-content" style="padding: 30px; color: #333333; line-height: 1.6;">
                                            <p style="margin: 0 0 20px 0; font-size: 16px;">Hola <strong>{org.name}</strong>,</p>
                                            
                                            <p style="margin: 0 0 20px 0; font-size: 15px;">Tu suscripción al plan <strong>{sub.plan.display_name}</strong> vence <strong>HOY</strong>.</p>
                                            
                                            <p style="margin: 0 0 25px 0; font-size: 15px;">Renueva inmediatamente para evitar el bloqueo de acceso a tus proyectos.</p>

                                            <!-- Botón CTA -->
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" class="button-container" style="margin: 0 0 25px 0;">
                                                <tr>
                                                    <td style="background-color: #c0392b; text-align: center;">
                                                        <a href="{settings.SITE_URL}/plans/subscription/" class="button-link" style="display: inline-block; padding: 14px 35px; font-size: 16px; color: #ffffff; text-decoration: none; font-weight: bold;">¡Renovar AHORA!</a>
                                                    </td>
                                                </tr>
                                            </table>

                                            <p style="margin: 20px 0 0 0; padding: 15px; background-color: #f8d7da; border: 1px solid #f5c6cb; text-align: center; font-size: 15px; color: #721c24; font-weight: bold;">⚠️ Acceso se bloqueará al finalizar el día</p>
                                        </td>
                                    </tr>

                                    <!-- Footer -->
                                    <tr>
                                        <td class="email-footer" style="background-color: #f5f5f5; padding: 20px; text-align: center; border-top: 1px solid #dddddd;">
                                            <p style="margin: 0; font-size: 14px; font-weight: bold; color: #333333;">{site_name}</p>
                                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #999999;">Sistema de Gestión de Proyectos</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                send_resend_email(user_email, subject, html)
                sent_count += 1

            self.stdout.write(self.style.SUCCESS(f'Recordatorios de renovación enviados: {sent_count}'))

        except Exception as e:
            logger.error(f"Error enviando recordatorios de renovación: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR('Error enviando recordatorios'))


