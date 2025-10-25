from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from uuid import uuid4
import logging
from core.structured_logging import log_error, log_warning, log_info, log_business_event

logger = logging.getLogger('apps.accounts')

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            log_warning(
                event="user_creation_missing_email",
                message="Intento de crear usuario sin email",
                logger_name='apps.accounts'
            )
            raise ValueError('El correo electrónico es obligatorio')
        
        email = self.normalize_email(email)
        org = extra_fields.get('organization')
        org_name = org.name if org else 'Sin organización'
        org_id = org.id if org else None
        
        # Solo loggear en desarrollo (DEBUG), evitar ruido en producción
        from django.conf import settings
        if settings.DEBUG:
            log_info(
                event="user_creation_started",
                message="Creando nuevo usuario",
                user_email=email,
                organization_name=org_name,
                logger_name='apps.accounts'
            )
        
        try:
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            
            # Business event importante: siempre loggear creación exitosa
            log_business_event(
                event="user_created",
                action="created",
                entity_type="user",
                entity_id=user.pk,
                user_email=email,
                organization_id=org_id,
                logger_name='apps.accounts'
            )
            return user
        except Exception as e:
            log_error(
                event="user_creation_failed",
                error_code="USR001",
                error_message=str(e),
                user_email=email,
                logger_name='apps.accounts'
            )
            raise

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            log_error(
                event="superuser_creation_failed",
                error_code="USR002",
                error_message="is_staff debe ser True",
                user_email=email,
                logger_name='apps.accounts'
            )
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            log_error(
                event="superuser_creation_failed",
                error_code="USR003",
                error_message="is_superuser debe ser True",
                user_email=email,
                logger_name='apps.accounts'
            )
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        try:
            user = self.create_user(email, password, **extra_fields)
            log_business_event(
                event="superuser_created",
                action="created",
                entity_type="superuser",
                entity_id=user.pk,
                user_email=email,
                logger_name='apps.accounts'
            )
            return user
        except Exception as e:
            log_error(
                event="superuser_creation_failed",
                error_code="USR004",
                error_message=str(e),
                user_email=email,
                logger_name='apps.accounts'
            )
            raise

class User(AbstractUser):
    username = models.CharField(
        "Username",
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        editable=False, 
        help_text="No requerido. Se genera a partir del email."
    )
    email = models.EmailField("Correo electrónico", unique=True)
    # Hacemos obligatorios first_name y last_name
    first_name = models.CharField(
        "Nombre", 
        max_length=50,
        help_text="Máximo 50 caracteres"
    )
    last_name = models.CharField(
        "Apellido", 
        max_length=50,
        help_text="Máximo 50 caracteres"
    )
    is_org_admin = models.BooleanField("Administrador de organización", default=False)
    password_change_required = models.BooleanField(
        "Cambio de contraseña requerido", 
        default=False,
        help_text="Si está marcado, el usuario deberá cambiar su contraseña en el próximo login."
    )
    organization = models.ForeignKey(
        'orgs.Organization', 
        on_delete=models.CASCADE, 
        related_name='users',
        verbose_name="Organización",
        null=True, 
        blank=True,
        help_text="Los usuarios se eliminarán automáticamente al eliminar la organización"
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_values = {}
        
        # Capturar valores anteriores para logging de cambios
        if not is_new:
            try:
                old_user = User.objects.get(pk=self.pk)
                old_values = {
                    'email': old_user.email,
                    'is_active': old_user.is_active,
                    'is_org_admin': old_user.is_org_admin,
                    'organization': old_user.organization.name if old_user.organization else None,
                    'password_change_required': old_user.password_change_required
                }
            except User.DoesNotExist:
                log_warning(
                    event="user_not_found_for_comparison",
                    message="Usuario no encontrado al intentar comparar cambios",
                    user_id=self.pk,
                    logger_name='apps.accounts'
                )
        
        if not self.username:
            # Generar un username simple para compatibilidad con Django
            # Usar el email como base con UUID corto para garantizar unicidad
            base_username = self.email.split('@')[0]
            unique_id = str(uuid4()).split('-')[0][:6]  # Un poco más largo para evitar colisiones
            self.username = f"{base_username}_{unique_id}"

        try:
            super().save(*args, **kwargs)
            
            # Solo loggear cambios importantes (no cada guardado)
            if is_new:
                # Business event: nuevo usuario
                from django.conf import settings
                if not settings.DEBUG:  # Solo en producción para auditoría
                    log_business_event(
                        event="user_saved",
                        action="created",
                        entity_type="user",
                        entity_id=self.pk,
                        user_email=self.email,
                        is_superuser=self.is_superuser,
                        is_org_admin=self.is_org_admin,
                        organization_id=self.organization_id,
                        logger_name='apps.accounts'
                    )
            else:
                # Log de cambios importantes solamente
                critical_changes = []
                if old_values.get('is_active') != self.is_active:
                    critical_changes.append(('status_change', 'activated' if self.is_active else 'deactivated'))
                if old_values.get('is_org_admin') != self.is_org_admin:
                    critical_changes.append(('role_change', 'promoted_to_admin' if self.is_org_admin else 'demoted_from_admin'))
                if old_values.get('organization') != (self.organization.name if self.organization else None):
                    critical_changes.append(('organization_change', f"{old_values.get('organization')} -> {self.organization.name if self.organization else None}"))
                
                # Solo loggear si hay cambios críticos
                if critical_changes:
                    log_business_event(
                        event="user_updated",
                        action="updated",
                        entity_type="user",
                        entity_id=self.pk,
                        user_email=self.email,
                        changes=str(critical_changes),
                        logger_name='apps.accounts'
                    )
                    
        except Exception as e:
            log_error(
                event="user_save_failed",
                error_code="USR005",
                error_message=str(e),
                user_email=self.email,
                user_id=self.pk,
                logger_name='apps.accounts'
            )
            raise

    def __str__(self):
        """Mostrar nombre completo o email como fallback"""
        return self.full_name
    
    @property
    def full_name(self):
        """Nombre completo del usuario con fallback robusto."""
        first = (self.first_name or '').strip()
        last = (self.last_name or '').strip()
        name = f"{first} {last}".strip()
        if not name:
            return self.email
        return name

    def get_full_name(self):
        """Compatibilidad con AbstractUser: retorna el nombre completo robusto."""
        return self.full_name
    
    @property
    def username_display(self):
        """Para compatibilidad con templates existentes"""
        return self.full_name
    
    def role_display(self):
        if self.is_org_admin:
            return "Administrador"
        else:
            return "Usuario"
    
    def can_manage_users(self):
        can_manage = self.is_org_admin
        if can_manage:
            logger.debug(f"Usuario {self.email} tiene permisos para gestionar usuarios")
        return can_manage
    
    def get_organization_name(self):
        return self.organization.name if self.organization else "Sin organización"
    
    def is_in_organization(self, org_id):
        return self.organization_id == org_id if self.organization else False
    
    def can_manage_organization(self):
        can_manage = self.is_org_admin and self.organization
        if can_manage:
            logger.debug(f"Usuario {self.email} tiene permisos para gestionar organización {self.organization.name}")
        return can_manage
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                name='unique_email'
            )
        ]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"