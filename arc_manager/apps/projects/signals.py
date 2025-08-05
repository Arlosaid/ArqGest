from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Phase

@receiver(post_save, sender=Task)
def update_phase_status_on_task_start(sender, instance, created, **kwargs):
    """
    Updates the phase status to 'In Progress' when one of its tasks starts.
    """
    if instance.status == Task.Status.IN_PROGRESS:
        phase = instance.phase
        if phase.status != Phase.Status.IN_PROGRESS:
            phase.status = Phase.Status.IN_PROGRESS
            phase.save()
