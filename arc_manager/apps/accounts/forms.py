from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
import logging
from core.validators import validate_password_spanish

logger = logging.getLogger('apps.accounts')

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Por favor, introduce un correo electrónico y contraseña válidos. '
                         'Ten en cuenta que ambos campos pueden ser sensibles a mayúsculas y minúsculas.',
        'inactive': 'Tu cuenta está inactiva. Por favor, contacta con el administrador de tu organización para reactivarla.',
        'org_inactive': 'Tu organización ha sido desactivada. Por favor, contacta con el soporte del sistema para más información.',
    }
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Recordarme por 30 días'
    )

    def clean_username(self):
        """Normalizar email a minúsculas y eliminar espacios para autenticación case-insensitive"""
        username = self.cleaned_data.get('username')
        if username:
            return username.strip().lower()
        return username

    def clean_password(self):
        """Eliminar espacios accidentales al inicio/final del password"""
        password = self.cleaned_data.get('password')
        if password:
            return password.strip()
        return password

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        # Verificar si el usuario existe y está inactivo o su organización está inactiva
        if username and password:
            try:
                User = get_user_model()
                # Búsqueda case-insensitive con organización precargada
                user = User.objects.select_related('organization').filter(email__iexact=username).first()
                
                if user:
                    # Verificar si la cuenta del usuario está inactiva
                    if not user.is_active:
                        logger.warning(
                            f"LOGIN BLOQUEADO - CUENTA INACTIVA | Email: {username} | "
                            f"Org: {user.get_organization_name()}",
                            extra={
                                'user_id': user.id,
                                'organization_id': user.organization_id if user.organization else None
                            }
                        )
                        raise ValidationError(
                            'Tu cuenta está inactiva. Por favor, contacta con el administrador de tu organización para reactivarla.',
                            code='inactive'
                        )
                    
                    # Verificar si la organización está inactiva (solo para usuarios no-superuser)
                    if user.organization and not user.organization.is_active and not user.is_superuser:
                        logger.warning(
                            f"LOGIN BLOQUEADO - ORGANIZACION INACTIVA | Email: {username} | "
                            f"Org: {user.organization.name} (ID: {user.organization.id}) | "
                            f"User ID: {user.id}",
                            extra={
                                'user_id': user.id,
                                'organization_id': user.organization.id
                            }
                        )
                        raise ValidationError(
                            'Tu organización ha sido desactivada. Por favor, contacta con el soporte del sistema para más información.',
                            code='org_inactive'
                        )
            except User.DoesNotExist:
                pass
        
        # El logging de login fallido se hace en views.py (form_invalid)
        return super().clean()


User = get_user_model()


class ForcePasswordChangeForm(forms.Form):
    """Formulario para cambio forzado de contraseña"""
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce tu contraseña actual'
        })
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce tu nueva contraseña'
        }),
        help_text="Tu contraseña debe tener al menos 8 caracteres y no puede ser completamente numérica."
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """Verificar que la contraseña actual sea correcta"""
        old_password = self.cleaned_data.get("old_password")
        
        logger.debug(f"Verificando contraseña actual para usuario: {self.user.email}")
        
        if not self.user.check_password(old_password):
            logger.warning(f"Contraseña actual incorrecta para usuario: {self.user.email}")
            raise ValidationError("La contraseña actual no es correcta.")
        
        logger.debug(f"Contraseña actual verificada exitosamente para: {self.user.email}")
        return old_password

    def clean_new_password1(self):
        """Validar la nueva contraseña usando validadores de Django"""
        password = self.cleaned_data.get('new_password1')
        
        logger.debug(f"Validando nueva contraseña para usuario: {self.user.email}")
        
        # Usar nuestro validador personalizado que traduce mensajes al español
        try:
            validate_password_spanish(password, user=self.user)
        except ValidationError as e:
            logger.warning(f"Nueva contraseña rechazada para {self.user.email}: {e.messages}")
            raise ValidationError(e.messages)
        
        logger.debug(f"Nueva contraseña válida para usuario: {self.user.email}")
        
        return password

    def clean(self):
        """Verificar que las nuevas contraseñas coincidan"""
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        old_password = cleaned_data.get("old_password")
        
        logger.debug(f"Validación final del formulario de cambio de contraseña para: {self.user.email}")

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                logger.warning(f"Las nuevas contraseñas no coinciden para usuario: {self.user.email}")
                raise ValidationError("Las nuevas contraseñas no coinciden.")
            
            # Verificar que no sea la misma contraseña actual
            if old_password and new_password1 == old_password:
                logger.warning(f"Usuario {self.user.email} intentó usar la misma contraseña actual")
                raise ValidationError("La nueva contraseña debe ser diferente a la actual.")
            
            logger.info(f"Formulario de cambio de contraseña validado exitosamente para: {self.user.email}")

        return cleaned_data


class SecureSetPasswordForm(SetPasswordForm):
    """Formulario de reset de contraseña que previene reusar la contraseña anterior"""
    
    def clean_new_password1(self):
        """Validar que la nueva contraseña sea diferente a la anterior y cumpla requisitos"""
        password = self.cleaned_data.get('new_password1')
        
        # Usar nuestro validador personalizado que traduce mensajes al español
        try:
            validate_password_spanish(password, user=self.user)
        except ValidationError as e:
            logger.warning(f"Password reset rechazado para {self.user.email}: {e.messages}")
            raise ValidationError(e.messages)
        
        # Verificar que la nueva contraseña no sea igual a la anterior
        if self.user and self.user.check_password(password):
            logger.warning(
                f"PASSWORD RESET BLOQUEADO | Email: {self.user.email} | "
                f"Razón: Intentó usar la misma contraseña anterior"
            )
            raise ValidationError(
                "Por seguridad, no puedes usar tu contraseña anterior. "
                "Por favor, elige una contraseña diferente.",
                code='password_same_as_old'
            )
        
        return password