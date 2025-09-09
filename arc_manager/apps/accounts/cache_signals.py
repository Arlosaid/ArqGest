"""
Signals para invalidar cache relacionado con usuarios y organizaciones
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def invalidate_user_cache_on_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda un usuario"""
    if instance.organization_id:
        # Invalidar cache de organización
        instance.organization.invalidate_user_cache()


@receiver(post_delete, sender=User)
def invalidate_user_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina un usuario"""
    if instance.organization_id:
        # Invalidar cache de organización
        instance.organization.invalidate_user_cache()
