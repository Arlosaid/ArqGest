"""
Signals para invalidar cache automáticamente cuando se modifican datos de organizaciones
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from .models import Client

logger = logging.getLogger(__name__)


def invalidate_client_related_cache(organization_id):
    """
    Invalida el cache relacionado con clientes.
    Se llama cuando se crea, modifica o elimina un Cliente.
    """
    cache_keys = [
        f"dashboard_stats:{organization_id}",
    ]
    cache.delete_many(cache_keys)
    logger.debug(f"Invalidated client cache for organization {organization_id}")


@receiver(post_save, sender=Client)
def invalidate_cache_on_client_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda un cliente"""
    if instance.organization_id:
        invalidate_client_related_cache(instance.organization_id)


@receiver(post_delete, sender=Client)
def invalidate_cache_on_client_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina un cliente"""
    if instance.organization_id:
        invalidate_client_related_cache(instance.organization_id)
