from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
import logging

logger = logging.getLogger('apps.accounts')

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Por favor, introduce un correo electrónico y contraseña válidos. '
                         'Ten en cuenta que ambos campos pueden ser sensibles a mayúsculas y minúsculas.',
        'inactive': 'Tu cuenta está inactiva. Por favor, contacta con el administrador de tu organización para reactivarla.',
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

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        logger.debug(f"Validando formulario de autenticación para: {username}")
        
        # Primero verificar si el usuario existe y está inactivo
        if username and password:
            try:
                User = get_user_model()
                user = User.objects.filter(email=username).first()
                
                if user and not user.is_active:
                    logger.warning(f"Intento de login con cuenta inactiva: {username}")
                    raise ValidationError(
                        'Tu cuenta está inactiva. Por favor, contacta con el administrador de tu organización para reactivarla.',
                        code='inactive'
                    )
            except User.DoesNotExist:
                pass
        
        try:
            result = super().clean()
            logger.debug(f"Validación exitosa para: {username}")
            return result
        except ValidationError as e:
            logger.warning(f"Error de validación en formulario de login - Usuario: {username}, Error: {str(e)}")
            
            # Si ocurre un error, asegúrate de que use los mensajes en español
            if hasattr(e, 'message') and e.message == 'Please enter a correct username and password. Note that both fields may be case-sensitive.':
                e.message = self.error_messages['invalid_login']
            raise e


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
        """Validar la nueva contraseña"""
        password = self.cleaned_data.get('new_password1')
        
        logger.debug(f"Validando nueva contraseña para usuario: {self.user.email}")
        
        validation_errors = []
        
        if len(password) < 8:
            validation_errors.append("menos de 8 caracteres")
            logger.warning(f"Nueva contraseña muy corta para {self.user.email}: {len(password)} caracteres")
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
            
        if password.isdigit():
            validation_errors.append("completamente numérica")
            logger.warning(f"Nueva contraseña completamente numérica para {self.user.email}")
            raise ValidationError("La contraseña no puede ser completamente numérica.")
        
        if not validation_errors:
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