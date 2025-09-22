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
    """Log cuando se crea un usuario nuevo"""
    if created:
        org_name = instance.organization.name if instance.organization else "Sin organización"
        role = "Superusuario" if instance.is_superuser else ("Admin de Org" if instance.is_org_admin else "Usuario")
        
        logger.info(
            f"Usuario creado exitosamente: {instance.email} (ID: {instance.pk}, {role}) "
            f"en {org_name} - Activo: {instance.is_active}"
        )
        
        # Log adicional para superusuarios (seguridad)
        if instance.is_superuser:
            logger.info(
                f"SUPERUSUARIO CREADO - Email: {instance.email}, "
                f"Nombre: {instance.get_full_name()}, ID: {instance.pk}"
            )
        
        # Log adicional para admins de organización
        if instance.is_org_admin:
            logger.info(
                f"ADMIN DE ORGANIZACIÓN CREADO - Email: {instance.email}, "
                f"Organización: {org_name}, ID: {instance.pk}"
            )


@receiver(pre_save, sender=User)
def log_user_changes(sender, instance, **kwargs):
    """Log cambios importantes en usuarios existentes"""
    if instance.pk:  # Solo para usuarios existentes
        try:
            old_instance = User.objects.get(pk=instance.pk)
            changes = []
            
            # Detectar cambios críticos
            if old_instance.is_active != instance.is_active:
                status = 'activado' if instance.is_active else 'desactivado'
                changes.append(f"usuario {status}")
                logger.info(f"Usuario {instance.email} ha sido {status}")
            
            if old_instance.is_org_admin != instance.is_org_admin:
                role_change = 'promovido a admin' if instance.is_org_admin else 'removido como admin'
                changes.append(f"rol: {role_change}")
                logger.info(f"Usuario {instance.email} - {role_change}")
            
            if old_instance.organization != instance.organization:
                old_org = old_instance.organization.name if old_instance.organization else 'Sin organización'
                new_org = instance.organization.name if instance.organization else 'Sin organización'
                changes.append(f"organización: {old_org} → {new_org}")
                logger.info(
                    f"Usuario {instance.email} transferido de {old_org} a {new_org}"
                )
            
            if old_instance.password_change_required != instance.password_change_required:
                pwd_status = 'requerido' if instance.password_change_required else 'no requerido'
                changes.append(f"cambio de contraseña: {pwd_status}")
                logger.info(
                    f"Cambio de contraseña {pwd_status} para usuario: {instance.email}"
                )
            
            # Log si hubo cambio de contraseña
            if old_instance.password != instance.password:
                logger.info(f"Contraseña cambiada para usuario: {instance.email}")
                changes.append("contraseña actualizada")
            
            if changes:
                logger.info(
                    f"Usuario modificado: {instance.email} - Cambios: {', '.join(changes)}"
                )
                
        except User.DoesNotExist:
            logger.warning(f"Usuario con ID {instance.pk} no encontrado para comparación de cambios")

