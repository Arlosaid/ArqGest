from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from apps.plans.models import Subscription
from core.email_utils import send_resend_email


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía recordatorios de renovación (T-2 y T-0) a organizaciones con suscripción próxima a vencer'

    def handle(self, *args, **options):
        try:
            window_days = getattr(settings, 'RENEWAL_WINDOW_DAYS', 2)
            now = timezone.now()

            # T-2 días (o ventana configurable)
            window_start = now
            window_end = now + timedelta(days=window_days)

            # Suscripciones activas que vencen en los próximos window_days
            subs_due = Subscription.objects.filter(
                end_date__gte=window_start,
                end_date__lte=window_end,
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            # T-0: vencen hoy
            start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_today = start_today + timedelta(days=1)
            subs_due_today = Subscription.objects.filter(
                end_date__gte=start_today,
                end_date__lt=end_today,
                subscription_status__in=['trial_active', 'basic_active']
            ).select_related('organization', 'plan')

            sent_count = 0

            for sub in subs_due:
                org = sub.organization
                user_email = getattr(org, 'owner_email', None) or getattr(org, 'contact_email', None)
                if not user_email:
                    continue

                subject = 'Recordatorio: Tu suscripción vence pronto'
                html = f"""
                <p>Hola {org.name},</p>
                <p>Tu suscripción al plan <strong>{sub.plan.display_name}</strong> vence el <strong>{sub.end_date.strftime('%d/%m/%Y')}</strong>.</p>
                <p>Puedes renovarla desde 2 días antes para evitar interrupciones.</p>
                <p><a href="{settings.SITE_URL}/plans/subscription/" style="background:#2d6cdf;color:#fff;padding:10px 14px;border-radius:6px;text-decoration:none;">Renovar ahora</a></p>
                <p>Gracias,<br/>Equipo ARC Manager</p>
                """
                send_resend_email(user_email, subject, html)
                sent_count += 1

            for sub in subs_due_today:
                org = sub.organization
                user_email = getattr(org, 'owner_email', None) or getattr(org, 'contact_email', None)
                if not user_email:
                    continue

                subject = 'Vence hoy: Renueva tu suscripción'
                html = f"""
                <p>Hola {org.name},</p>
                <p>Tu suscripción al plan <strong>{sub.plan.display_name}</strong> vence <strong>hoy</strong>.</p>
                <p>Renueva para evitar el bloqueo de acceso.</p>
                <p><a href="{settings.SITE_URL}/plans/subscription/" style="background:#c0392b;color:#fff;padding:10px 14px;border-radius:6px;text-decoration:none;">Renovar ahora</a></p>
                <p>Gracias,<br/>Equipo ARC Manager</p>
                """
                send_resend_email(user_email, subject, html)
                sent_count += 1

            self.stdout.write(self.style.SUCCESS(f'Recordatorios de renovación enviados: {sent_count}'))

        except Exception as e:
            logger.error(f"Error enviando recordatorios de renovación: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR('Error enviando recordatorios'))


