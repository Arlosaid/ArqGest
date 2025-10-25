from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import User
from core.structured_logging import log_info, log_warning
 
# NOTA: Los logs de estos signals se reducen al mínimo.
# Los eventos de negocio se loguean desde las views donde ocurren.


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
    """Log creación de usuarios críticos (superusers y admins) - SOLO eventos de seguridad"""
    if created:
        # Solo loguear creación de superusers (crítico para seguridad)
        if instance.is_superuser:
            log_warning(
                event="superuser_created",
                message=f"SUPERUSUARIO CREADO - {instance.email}",
                user_id=instance.pk,
                user_email=instance.email,
                logger_name='django.security'
            )
        # Los admins de org NO se loguean aquí, se loguean desde la view donde se crean


@receiver(pre_save, sender=User)
def log_user_changes(sender, instance, **kwargs):
    """Log solo cambios críticos de seguridad en usuarios existentes"""
    if instance.pk:  # Solo para usuarios existentes
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Solo loguear cambios de permisos CRÍTICOS (superuser)
            if old_instance.is_superuser != instance.is_superuser:
                role_change = 'promovido a superusuario' if instance.is_superuser else 'removido como superusuario'
                log_warning(
                    event="superuser_role_changed",
                    message=f"CAMBIO CRÍTICO: Usuario {instance.email} - {role_change}",
                    user_id=instance.pk,
                    user_email=instance.email,
                    old_is_superuser=old_instance.is_superuser,
                    new_is_superuser=instance.is_superuser,
                    logger_name='django.security'
                )
            # Los cambios de is_org_admin NO se loguean aquí (no son críticos de seguridad)
                
        except User.DoesNotExist:
            pass

