"""
Validadores personalizados de contraseña más coherentes y menos restrictivos.

Estos validadores reemplazan los validadores de Django por defecto para ofrecer:
- Mensajes claros y coherentes
- Validaciones más razonables (no tan estrictas)
- Mejor experiencia de usuario
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class BasePasswordValidator:
    """
    Clase base para validadores de contraseña.
    """
    def validate(self, password, user=None):
        """
        Validar la contraseña. Debe ser implementado por las subclases.
        """
        raise NotImplementedError
    
    def get_help_text(self):
        """
        Retorna texto de ayuda para el validador.
        """
        return ""


class CustomMinimumLengthValidator(BasePasswordValidator):
    """
    Validador de longitud mínima personalizado.
    Por defecto: 8 caracteres (puede configurarse).
    """
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("La contraseña debe tener al menos %(min_length)d caracteres.") % {
                    'min_length': self.min_length
                },
                code='password_too_short',
                params={'min_length': self.min_length},
            )
    
    def get_help_text(self):
        return _("Tu contraseña debe contener al menos %(min_length)d caracteres.") % {
            'min_length': self.min_length
        }


class CustomUserAttributeSimilarityValidator(BasePasswordValidator):
    """
    Validador de similitud con atributos del usuario más flexible.
    No rechaza si es ligeramente similar, solo si es muy similar.
    """
    def __init__(self, user_attributes=None, max_similarity=0.9):
        """
        Args:
            user_attributes: Atributos del usuario a verificar (email, username, etc.)
            max_similarity: Similitud máxima permitida (0-1). Mayor = más flexible.
        """
        self.user_attributes = user_attributes or ['email', 'username']
        self.max_similarity = max_similarity
    
    def _similarity(self, a, b):
        """
        Calcula similitud entre dos strings usando SequenceMatcher.
        0 = completamente diferentes, 1 = idénticas
        """
        from difflib import SequenceMatcher
        return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()
    
    def validate(self, password, user=None):
        if not user:
            return
        
        # Verificar contra atributos del usuario con umbral más flexible
        password_lower = password.lower()
        
        # Verificar email
        if hasattr(user, 'email') and user.email:
            email_parts = user.email.split('@')[0].lower()  # Usar solo la parte antes de @
            similarity = self._similarity(password_lower, email_parts)
            if similarity > self.max_similarity:
                raise ValidationError(
                    _("La contraseña es demasiado similar a tu correo electrónico."),
                    code='password_too_similar_email',
                )
        
        # Verificar username
        if hasattr(user, 'username') and user.username:
            similarity = self._similarity(password_lower, user.username.lower())
            if similarity > self.max_similarity:
                raise ValidationError(
                    _("La contraseña es demasiado similar a tu nombre de usuario."),
                    code='password_too_similar_username',
                )
    
    def get_help_text(self):
        return _("Tu contraseña no puede ser similar a tu email o nombre de usuario.")


class CustomNumericPasswordValidator(BasePasswordValidator):
    """
    Validador numérico personalizado.
    Rechaza si la contraseña es COMPLETAMENTE numérica.
    """
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _("La contraseña no puede ser completamente numérica."),
                code='password_entirely_numeric',
            )
    
    def get_help_text(self):
        return _("Tu contraseña no puede contener solo números.")


class PasswordComplexityValidator(BasePasswordValidator):
    """
    Validador personalizado que verifica la complejidad mínima de la contraseña.
    
    Requiere:
    - Al menos 1 número
    - Variedad de caracteres (mayúscula, minúscula, o ambos)
    """
    def __init__(self, min_numbers=1):
        self.min_numbers = min_numbers
    
    def validate(self, password, user=None):
        """
        Validar que la contraseña tenga suficiente complejidad.
        """
        errors = []
        
        # Contar números
        numbers_count = sum(1 for c in password if c.isdigit())
        
        # Validar requisitos
        if numbers_count < self.min_numbers:
            errors.append(
                _("La contraseña debe incluir al menos un número.")
            )
        
        if errors:
            raise ValidationError(errors, code='password_not_complex_enough')
    
    def get_help_text(self):
        return _("La contraseña debe incluir al menos un número.")


class WeakPasswordValidator(BasePasswordValidator):
    """
    Validador que rechaza contraseñas demasiado débiles o predecibles.
    
    Rechaza:
    - Patrones de teclado secuencial (qwerty, asdfgh, etc.)
    - Números secuenciales MUY obvios como ÚNICA PARTE (123456, 654321)
    
    Nota: No usa la lista exhaustiva de CommonPasswordValidator de Django,
    que es muy restrictiva.
    """
    def __init__(self):
        # Patrones de teclado secuencial - EXACTOS
        self.keyboard_patterns = [
            'qwerty', 'asdfgh', 'zxcvbn', 'qazwsx', 'qweasd',
        ]
    
    def validate(self, password, user=None):
        password_lower = password.lower()
        
        # Verificar patrones de teclado EXACTOS
        for pattern in self.keyboard_patterns:
            if pattern in password_lower:
                raise ValidationError(
                    _("La contraseña contiene un patrón de teclado demasiado predecible."),
                    code='password_keyboard_pattern',
                )
    
    def get_help_text(self):
        return _("Evita patrones de teclado muy predecibles (como qwerty, asdfgh).")
