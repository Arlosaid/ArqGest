from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Por favor, introduce un correo electrónico y contraseña válidos. '
                         'Ten en cuenta que ambos campos pueden ser sensibles a mayúsculas y minúsculas.',
        'inactive': 'Esta cuenta está inactiva.',
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

    def clean(self):
        try:
            return super().clean()
        except ValidationError as e:
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
        if not self.user.check_password(old_password):
            raise ValidationError("La contraseña actual no es correcta.")
        return old_password

    def clean_new_password1(self):
        """Validar la nueva contraseña"""
        password = self.cleaned_data.get('new_password1')
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if password.isdigit():
            raise ValidationError("La contraseña no puede ser completamente numérica.")
        return password

    def clean(self):
        """Verificar que las nuevas contraseñas coincidan"""
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("Las nuevas contraseñas no coinciden.")
            
            # Verificar que no sea la misma contraseña actual
            old_password = cleaned_data.get("old_password")
            if old_password and new_password1 == old_password:
                raise ValidationError("La nueva contraseña debe ser diferente a la actual.")

        return cleaned_data