from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Task, Phase
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Task)
def update_phase_status_on_task_change(sender, instance, created, **kwargs):
    """
    Actualiza automáticamente el estado de la fase basado en sus tareas:
    - PENDING: No hay tareas o todas están en TODO
    - IN_PROGRESS: Al menos una tarea está en progreso o hay tareas activas
    - COMPLETED: Todas las tareas están completadas
    """
    phase = instance.phase
    
    # Obtener todas las tareas de la fase
    tasks = phase.tasks.all()
    total_tasks = tasks.count()
    
    if total_tasks == 0:
        # Sin tareas, la fase debe estar pendiente
        new_status = Phase.Status.PENDING
    else:
        # Contar tareas por estado
        done_count = tasks.filter(status=Task.Status.DONE).count()
        in_progress_count = tasks.filter(status=Task.Status.IN_PROGRESS).count()
        paused_count = tasks.filter(status=Task.Status.PAUSED).count()
        
        if done_count == total_tasks:
            # Todas las tareas completadas
            new_status = Phase.Status.COMPLETED
        elif in_progress_count > 0 or paused_count > 0 or done_count > 0:
            # Al menos una tarea en progreso, pausada o completada
            new_status = Phase.Status.IN_PROGRESS
        else:
            # Todas las tareas están en TODO
            new_status = Phase.Status.PENDING
    
    # Actualizar el estado si cambió
    if phase.status != new_status:
        old_status = phase.status
        phase.status = new_status
        phase.save()
        logger.info(
            "phase_auto_status_changed",
            extra={
                "event": "phase_auto_status_changed",
                "phase_id": phase.id,
                "phase_name": phase.name,
                "old_status": old_status,
                "new_status": new_status,
                "total_tasks": total_tasks,
                "done_tasks": done_count if 'done_count' in locals() else 0,
                "trigger_task_id": instance.id,
                "trigger_task_status": instance.status
            }
        )

@receiver(post_delete, sender=Task)
def update_phase_status_on_task_delete(sender, instance, **kwargs):
    """
    Actualiza el estado de la fase cuando se elimina una tarea.
    """
    try:
        phase = instance.phase
        
        # Obtener tareas restantes
        tasks = phase.tasks.all()
        total_tasks = tasks.count()
        
        if total_tasks == 0:
            # Sin tareas, volver a PENDING
            new_status = Phase.Status.PENDING
        else:
            # Recalcular estado
            done_count = tasks.filter(status=Task.Status.DONE).count()
            in_progress_count = tasks.filter(status=Task.Status.IN_PROGRESS).count()
            paused_count = tasks.filter(status=Task.Status.PAUSED).count()
            
            if done_count == total_tasks:
                new_status = Phase.Status.COMPLETED
            elif in_progress_count > 0 or paused_count > 0 or done_count > 0:
                new_status = Phase.Status.IN_PROGRESS
            else:
                new_status = Phase.Status.PENDING
        
        # Actualizar si cambió
        if phase.status != new_status:
            old_status = phase.status
            phase.status = new_status
            phase.save()
            logger.info(
                "phase_auto_status_changed_after_delete",
                extra={
                    "event": "phase_auto_status_changed_after_delete",
                    "phase_id": phase.id,
                    "phase_name": phase.name,
                    "old_status": old_status,
                    "new_status": new_status,
                    "remaining_tasks": total_tasks,
                    "deleted_task_id": instance.id
                }
            )
    except Phase.DoesNotExist:
        # La fase ya fue eliminada, no hacer nada
        pass


