from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from uuid import uuid4
import logging

logger = logging.getLogger('apps.accounts')

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            logger.warning(f"Intento de crear usuario sin email. Extra fields: {extra_fields}")
            raise ValueError('El correo electrónico es obligatorio')
        
        email = self.normalize_email(email)
        org_name = extra_fields.get('organization', {}).name if extra_fields.get('organization') else 'Sin organización'
        
        logger.info(f"Creando nuevo usuario: {email} en organización: {org_name}")
        
        try:
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            
            logger.info(f"Usuario creado exitosamente: {email} (ID: {user.pk})")
            return user
        except Exception as e:
            logger.error(f"Error al crear usuario {email}: {str(e)}")
            raise

    def create_superuser(self, email, password=None, **extra_fields):
        logger.info(f"Creando superusuario: {email}")
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            logger.error(f"Error al crear superusuario {email}: is_staff debe ser True")
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            logger.error(f"Error al crear superusuario {email}: is_superuser debe ser True")
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        try:
            user = self.create_user(email, password, **extra_fields)
            logger.info(f"Superusuario creado exitosamente: {email} (ID: {user.pk})")
            return user
        except Exception as e:
            logger.error(f"Error al crear superusuario {email}: {str(e)}")
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
                logger.warning(f"Usuario con ID {self.pk} no encontrado para comparación")
        
        if not self.username:
            # Generar un username simple para compatibilidad con Django
            # Usar el email como base con UUID corto para garantizar unicidad
            base_username = self.email.split('@')[0]
            unique_id = str(uuid4()).split('-')[0][:6]  # Un poco más largo para evitar colisiones
            self.username = f"{base_username}_{unique_id}"

        try:
            super().save(*args, **kwargs)
            
            # Logging de cambios específicos
            if is_new:
                org_name = self.organization.name if self.organization else 'Sin organización'
                role = 'Superusuario' if self.is_superuser else ('Admin de Org' if self.is_org_admin else 'Usuario')
                logger.info(f"Nuevo usuario guardado: {self.email} ({role}) - Organización: {org_name}")
            else:
                # Log de cambios importantes
                changes = []
                if old_values.get('email') != self.email:
                    changes.append(f"email: {old_values.get('email')} → {self.email}")
                if old_values.get('is_active') != self.is_active:
                    status = 'activado' if self.is_active else 'desactivado'
                    changes.append(f"usuario {status}")
                if old_values.get('is_org_admin') != self.is_org_admin:
                    role_change = 'promovido a admin' if self.is_org_admin else 'removido como admin'
                    changes.append(f"rol: {role_change}")
                if old_values.get('organization') != (self.organization.name if self.organization else None):
                    old_org = old_values.get('organization') or 'Sin organización'
                    new_org = self.organization.name if self.organization else 'Sin organización'
                    changes.append(f"organización: {old_org} → {new_org}")
                if old_values.get('password_change_required') != self.password_change_required:
                    pwd_status = 'requerido' if self.password_change_required else 'no requerido'
                    changes.append(f"cambio de contraseña: {pwd_status}")
                
                if changes:
                    logger.info(f"Usuario actualizado {self.email} (ID: {self.pk}): {', '.join(changes)}")
                    
        except Exception as e:
            logger.error(f"Error al guardar usuario {self.email}: {str(e)}")
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