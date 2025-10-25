from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Phase
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Task)
def update_phase_status_on_task_start(sender, instance, created, **kwargs):
    """
    Updates the phase status to 'In Progress' when one of its tasks starts.
    """
    if instance.status == Task.Status.IN_PROGRESS:
        phase = instance.phase
        if phase.status != Phase.Status.IN_PROGRESS:
            old_status = phase.status
            phase.status = Phase.Status.IN_PROGRESS
            phase.save()
            logger.info(
                "phase_auto_status_changed",
                extra={
                    "event": "phase_auto_status_changed",
                    "phase_id": phase.id,
                    "phase_name": phase.name,
                    "old_status": old_status,
                    "new_status": "IN_PROGRESS",
                    "trigger_task_id": instance.id
                }
            )
    
    # Eliminado: log de creación de tarea (redundante con models.py)
    # Eliminado: log DEBUG de actualización (ruido innecesario)

