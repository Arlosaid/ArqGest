"""
Signals para invalidar cache automáticamente cuando se modifican datos
"""
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Project, Task, Phase
from .cache_utils import invalidate_project_cache, invalidate_task_cache


@receiver(post_save, sender=Project)
def invalidate_project_cache_on_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda un proyecto"""
    if instance.organization_id:
        invalidate_project_cache(instance.organization_id, instance.id)


@receiver(post_delete, sender=Project)
def invalidate_project_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina un proyecto"""
    if instance.organization_id:
        invalidate_project_cache(instance.organization_id, instance.id)


@receiver(post_save, sender=Task)
def invalidate_task_cache_on_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda una tarea"""
    if instance.phase and instance.phase.project:
        project = instance.phase.project
        user_id = instance.assigned_to_id if instance.assigned_to else None
        invalidate_task_cache(project.organization_id, project.id, user_id)


@receiver(post_delete, sender=Task)
def invalidate_task_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina una tarea"""
    if instance.phase and instance.phase.project:
        project = instance.phase.project
        user_id = instance.assigned_to_id if instance.assigned_to else None
        invalidate_task_cache(project.organization_id, project.id, user_id)


@receiver(post_save, sender=Phase)
def invalidate_phase_cache_on_save(sender, instance, **kwargs):
    """Invalida cache cuando se guarda una fase"""
    if instance.project:
        invalidate_project_cache(instance.project.organization_id, instance.project.id)


@receiver(post_delete, sender=Phase)
def invalidate_phase_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina una fase"""
    if instance.project:
        invalidate_project_cache(instance.project.organization_id, instance.project.id)
