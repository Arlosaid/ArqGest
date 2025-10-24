# apps/main/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SystemSettings
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SystemSettings)
def sync_plans_on_settings_change(sender, instance, created, **kwargs):
    """
    Sincroniza automáticamente los planes cuando se guarda SystemSettings.
    Solo sincroniza si se modificaron campos relacionados con planes.
    """
    # Evitar imports circulares
    from apps.plans.models import Plan
    
    try:
        # Actualizar Plan Trial
        trial_plan = Plan.objects.filter(name='trial', is_active=True).first()
        if trial_plan:
            trial_updated = False
            if trial_plan.max_users != instance.max_users_trial:
                trial_plan.max_users = instance.max_users_trial
                trial_updated = True
            if trial_plan.max_storage_gb != instance.storage_trial_gb:
                trial_plan.max_storage_gb = instance.storage_trial_gb
                trial_updated = True
            if trial_plan.trial_days != instance.trial_duration_days:
                trial_plan.trial_days = instance.trial_duration_days
                trial_updated = True
                
            if trial_updated:
                trial_plan.save()
                logger.info(f"Plan Trial sincronizado automáticamente: {trial_plan.max_users} usuarios, {trial_plan.max_storage_gb} GB")
        
        # Actualizar Plan Básico
        basic_plan = Plan.objects.filter(name='basic', is_active=True).first()
        if basic_plan:
            basic_updated = False
            if basic_plan.max_users != instance.max_users_basic:
                basic_plan.max_users = instance.max_users_basic
                basic_updated = True
            if basic_plan.max_storage_gb != instance.storage_basic_gb:
                basic_plan.max_storage_gb = instance.storage_basic_gb
                basic_updated = True
            if basic_plan.grace_period_days != instance.grace_period_days:
                basic_plan.grace_period_days = instance.grace_period_days
                basic_updated = True
                
            if basic_updated:
                basic_plan.save()
                logger.info(f"Plan Básico sincronizado automáticamente: {basic_plan.max_users} usuarios, {basic_plan.max_storage_gb} GB")
                
    except Exception as e:
        logger.error(f"Error sincronizando planes automáticamente: {e}", exc_info=True)

