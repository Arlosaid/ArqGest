"""
Signals para invalidar cache automáticamente cuando se modifican solicitudes de planes
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from .models import RenewalRequest, UpgradeRequest

logger = logging.getLogger(__name__)


def invalidate_pending_requests_cache(organization_id):
    """
    Invalida el cache de solicitudes pendientes para una organización.
    Se llama cuando se crea, modifica o elimina una RenewalRequest o UpgradeRequest.
    """
    cache_key = f"org_pending_requests:{organization_id}"
    cache.delete(cache_key)
    logger.debug(f"Invalidated pending requests cache for organization {organization_id}")


@receiver(post_save, sender=RenewalRequest)
def invalidate_cache_on_renewal_request_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda una solicitud de renovación"""
    if instance.organization_id:
        invalidate_pending_requests_cache(instance.organization_id)


@receiver(post_delete, sender=RenewalRequest)
def invalidate_cache_on_renewal_request_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina una solicitud de renovación"""
    if instance.organization_id:
        invalidate_pending_requests_cache(instance.organization_id)


@receiver(post_save, sender=UpgradeRequest)
def invalidate_cache_on_upgrade_request_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda una solicitud de upgrade"""
    if instance.organization_id:
        invalidate_pending_requests_cache(instance.organization_id)


@receiver(post_delete, sender=UpgradeRequest)
def invalidate_cache_on_upgrade_request_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina una solicitud de upgrade"""
    if instance.organization_id:
        invalidate_pending_requests_cache(instance.organization_id)
