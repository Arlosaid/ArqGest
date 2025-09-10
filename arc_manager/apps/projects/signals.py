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
            logger.info(f"Phase {phase.id} ('{phase.name}') status automatically updated from '{old_status}' to 'IN_PROGRESS' due to task {instance.id} starting")
    
    if created:
        logger.info(f"New task created - ID: {instance.id}, Title: '{instance.title}', Phase: {instance.phase.id}, Project: {instance.phase.project.id}")
    else:
        logger.debug(f"Task updated - ID: {instance.id}, Status: {instance.status}, Title: '{instance.title}'")
