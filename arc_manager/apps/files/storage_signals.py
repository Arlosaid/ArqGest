# apps/files/storage_signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProjectFile
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ProjectFile)
def invalidate_storage_cache_on_save(sender, instance, created, **kwargs):
    """Invalida el cache de almacenamiento cuando se guarda un archivo"""
    try:
        from apps.orgs.storage_service import StorageService
        organization_id = instance.phase.project.organization.id
        StorageService.invalidate_cache(organization_id)
        
        if created:
            logger.debug(f"Storage cache invalidated for org {organization_id} - new file added")
        else:
            logger.debug(f"Storage cache invalidated for org {organization_id} - file updated")
    except Exception as e:
        logger.error(f"Error invalidating storage cache on file save: {str(e)}")

@receiver(post_delete, sender=ProjectFile)
def invalidate_storage_cache_on_delete(sender, instance, **kwargs):
    """Invalida el cache de almacenamiento cuando se elimina un archivo"""
    try:
        from apps.orgs.storage_service import StorageService
        organization_id = instance.phase.project.organization.id
        StorageService.invalidate_cache(organization_id)
        
        logger.debug(f"Storage cache invalidated for org {organization_id} - file deleted")
    except Exception as e:
        logger.error(f"Error invalidating storage cache on file delete: {str(e)}")
