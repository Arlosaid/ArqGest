from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import User
import logging
 
# Configurar logger del módulo
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def validate_user_organization(sender, instance, **kwargs):
    """Validar que usuarios activos tengan organización (excepto superusers)"""
    if (instance.is_active and 
        not instance.is_superuser and 
        not instance.organization):
        raise ValidationError(
            "Los usuarios activos deben tener una organización asignada"
        )


@receiver(pre_save, sender=User)
def validate_organization_limits(sender, instance, **kwargs):
    """Validar límites de organización al crear/editar usuarios"""
    if (instance.organization and 
        instance.is_active and 
        not instance.pk):  # Solo para nuevos usuarios
        
        if not instance.organization.can_add_user():
            raise ValidationError(
                f"La organización {instance.organization.name} "
                f"ha alcanzado su límite de usuarios"
            )


# El signal auto_generate_username ya no es necesario porque eliminamos el campo username


@receiver(pre_save, sender=User)
def ensure_names_present(sender, instance, **kwargs):
    """Asegurar que los usuarios tengan nombre y apellido"""
    if not instance.first_name or not instance.last_name:
        # Si no tiene nombres, usar el email para generar nombres por defecto
        if instance.email and not instance.first_name and not instance.last_name:
            email_part = instance.email.split('@')[0]
            
            # Si el email contiene punto, separar en nombre y apellido
            if '.' in email_part:
                parts = email_part.split('.')
                if len(parts) >= 2:
                    instance.first_name = parts[0].capitalize()
                    instance.last_name = parts[1].capitalize()
            else:
                # Solo usar como nombre
                instance.first_name = email_part.capitalize()
                instance.last_name = "Usuario"  # Apellido por defecto


@receiver(pre_save, sender=User)
def validate_admin_without_org(sender, instance, **kwargs):
    """Validar que admins de org tengan organización"""
    if (instance.is_org_admin and 
        not instance.organization and 
        not instance.is_superuser):
        raise ValidationError(
            "Los administradores de organización deben tener una organización asignada"
        )


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log creación de usuarios críticos (superusers y admins)"""
    if created:
        # Solo loguear creación de usuarios con permisos elevados (seguridad)
        if instance.is_superuser:
            logger.info(
                f"SUPERUSUARIO CREADO - Email: {instance.email}, "
                f"Nombre: {instance.get_full_name()}, ID: {instance.pk}"
            )
        elif instance.is_org_admin:
            org_name = instance.organization.name if instance.organization else "Sin organización"
            logger.info(
                f"ADMIN DE ORGANIZACIÓN CREADO - Email: {instance.email}, "
                f"Organización: {org_name}, ID: {instance.pk}"
            )


@receiver(pre_save, sender=User)
def log_user_changes(sender, instance, **kwargs):
    """Log solo cambios críticos de seguridad en usuarios existentes"""
    if instance.pk:  # Solo para usuarios existentes
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Solo loguear cambios de permisos y seguridad críticos
            if old_instance.is_org_admin != instance.is_org_admin:
                role_change = 'promovido a admin' if instance.is_org_admin else 'removido como admin'
                logger.info(f"Usuario {instance.email} - {role_change}")
            
            if old_instance.is_superuser != instance.is_superuser:
                role_change = 'promovido a superusuario' if instance.is_superuser else 'removido como superusuario'
                logger.warning(f"CAMBIO CRÍTICO: Usuario {instance.email} - {role_change}")
                
        except User.DoesNotExist:
            pass

