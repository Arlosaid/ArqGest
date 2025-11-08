"""
Signals para eventos de seguridad de Django Axes.
"""
from django.dispatch import receiver
from axes.signals import user_locked_out
import logging

logger = logging.getLogger('apps.accounts')


@receiver(user_locked_out)
def log_user_lockout(sender, request, username, ip_address, **kwargs):
    """
    Signal que se ejecuta cuando Axes bloquea a un usuario.
    
    Este es el log más importante para detectar ataques de fuerza bruta.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:200] if request else 'N/A'
    
    # Log CRÍTICO nivel WARNING para que aparezca en alertas de producción
    logger.warning(
        f"BLOQUEO POR FUERZA BRUTA | "
        f"Email: {username} | "
        f"IP: {ip_address} | "
        f"User-Agent: {user_agent} | "
        f"Cooloff: 15 minutos"
    )
