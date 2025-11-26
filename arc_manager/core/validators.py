"""
Validadores personalizados para toda la aplicación.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password as django_validate_password
from decimal import Decimal, InvalidOperation
import re
from datetime import date, datetime


# ============================================
# VALIDADORES DE NOMBRES
# ============================================

def validate_name_length(value, max_length, field_name="nombre"):
    """
    Valida que un nombre no exceda la longitud máxima.
    
    Args:
        value: El valor a validar
        max_length: Longitud máxima permitida
        field_name: Nombre del campo para el mensaje de error
    """
    if len(value) > max_length:
        raise ValidationError(
            _(f"El {field_name} no puede exceder {max_length} caracteres. "
              f"Actualmente tiene {len(value)} caracteres."),
            code='max_length_exceeded'
        )


def validate_name_not_empty(value, field_name="nombre"):
    """
    Valida que un nombre no esté vacío o solo contenga espacios.
    
    Args:
        value: El valor a validar
        field_name: Nombre del campo para el mensaje de error
    """
    if not value or not value.strip():
        raise ValidationError(
            _(f"El {field_name} no puede estar vacío."),
            code='empty_name'
        )


def validate_name_characters(value, field_name="nombre"):
    """
    Valida que un nombre solo contenga caracteres permitidos.
    Permite letras, números, espacios y algunos caracteres especiales comunes.
    
    Args:
        value: El valor a validar
        field_name: Nombre del campo para el mensaje de error
    """
    # Permite letras (incluyendo acentos), números, espacios, guiones, puntos, comas, paréntesis
    pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-\.\,\(\)\_\&\/]+$'
    
    if not re.match(pattern, value):
        raise ValidationError(
            _(f"El {field_name} contiene caracteres no permitidos. "
              f"Use solo letras, números, espacios y caracteres básicos (-, ., _, &, /)."),
            code='invalid_characters'
        )


def validate_no_multiple_spaces(value, field_name="nombre"):
    """
    Valida que no haya múltiples espacios consecutivos.
    
    Args:
        value: El valor a validar
        field_name: Nombre del campo para el mensaje de error
    """
    if '  ' in value:
        raise ValidationError(
            _(f"El {field_name} no debe contener múltiples espacios consecutivos."),
            code='multiple_spaces'
        )


def validate_project_name(value):
    """Validador específico para nombres de proyectos."""
    validate_name_not_empty(value, "nombre del proyecto")
    validate_name_length(value, 100, "nombre del proyecto")
    validate_name_characters(value, "nombre del proyecto")
    validate_no_multiple_spaces(value, "nombre del proyecto")


def validate_task_title(value):
    """Validador específico para títulos de tareas."""
    validate_name_not_empty(value, "título de la tarea")
    validate_name_length(value, 120, "título de la tarea")
    validate_name_characters(value, "título de la tarea")
    validate_no_multiple_spaces(value, "título de la tarea")


def validate_client_name(value):
    """Validador específico para nombres de clientes."""
    validate_name_not_empty(value, "nombre del cliente")
    validate_name_length(value, 100, "nombre del cliente")
    validate_name_characters(value, "nombre del cliente")
    validate_no_multiple_spaces(value, "nombre del cliente")


def validate_organization_name(value):
    """Validador específico para nombres de organizaciones."""
    validate_name_not_empty(value, "nombre de la organización")
    validate_name_length(value, 100, "nombre de la organización")
    validate_name_characters(value, "nombre de la organización")
    validate_no_multiple_spaces(value, "nombre de la organización")


def validate_user_name(value):
    """Validador específico para nombres de usuarios."""
    validate_name_not_empty(value, "nombre")
    validate_name_length(value, 50, "nombre")
    # Para nombres de personas, usar validación más estricta (solo letras y espacios)
    pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("El nombre solo debe contener letras, espacios y guiones."),
            code='invalid_characters'
        )
    validate_no_multiple_spaces(value, "nombre")


def validate_phase_name(value):
    """Validador específico para nombres de fases."""
    validate_name_not_empty(value, "nombre de la fase")
    validate_name_length(value, 100, "nombre de la fase")
    validate_name_characters(value, "nombre de la fase")
    validate_no_multiple_spaces(value, "nombre de la fase")


# ============================================
# VALIDADORES DE TELÉFONO
# ============================================

def validate_phone_number(value):
    """
    Valida formato de número telefónico.
    Acepta formatos internacionales comunes.
    """
    if not value:
        return  # Permitir vacío si el campo es opcional
    
    # Limpiar el número (quitar espacios, guiones, paréntesis)
    cleaned = re.sub(r'[\s\-\(\)\.]', '', value)
    
    # Validar que solo contenga números y opcionalmente un + al inicio
    pattern = r'^\+?[0-9]{8,15}$'
    
    if not re.match(pattern, cleaned):
        raise ValidationError(
            _("Introduce un número de teléfono válido. "
              "Formato: +52 123 456 7890 o 1234567890 (8-15 dígitos)"),
            code='invalid_phone'
        )


# ============================================
# VALIDADORES DE EMAIL
# ============================================

def validate_business_email(value):
    """
    Valida que el email tenga un formato válido y sugiere dominios profesionales.
    """
    # Primero validar con el validador estándar de Django
    email_validator = EmailValidator(message=_("Introduce un email válido."))
    email_validator(value)
    
    # Lista de dominios temporales/desechables comunes (opcional)
    disposable_domains = [
        'tempmail.com', 'throwaway.email', '10minutemail.com',
        'guerrillamail.com', 'mailinator.com'
    ]
    
    domain = value.split('@')[1].lower() if '@' in value else ''
    
    if domain in disposable_domains:
        raise ValidationError(
            _("Por favor usa un email permanente, no temporal."),
            code='disposable_email'
        )


# ============================================
# VALIDADORES DE FECHAS
# ============================================

def validate_date_not_too_far_future(value, years=10):
    """
    Valida que una fecha no esté demasiado lejos en el futuro.
    """
    if not value:
        return
    
    from datetime import timedelta
    max_future = date.today() + timedelta(days=365 * years)
    
    if value > max_future:
        raise ValidationError(
            _(f"La fecha no puede ser más de {years} años en el futuro."),
            code='date_too_far'
        )


def validate_date_not_too_old(value, years=50):
    """
    Valida que una fecha no sea demasiado antigua.
    """
    if not value:
        return
    
    from datetime import timedelta
    min_past = date.today() - timedelta(days=365 * years)
    
    if value < min_past:
        raise ValidationError(
            _(f"La fecha no puede ser más de {years} años en el pasado."),
            code='date_too_old'
        )


def validate_end_date_after_start_date(start_date, end_date):
    """
    Valida que la fecha de fin sea posterior a la de inicio.
    """
    if start_date and end_date and end_date < start_date:
        raise ValidationError(
            _("La fecha de fin debe ser posterior a la fecha de inicio."),
            code='invalid_date_range'
        )


# ============================================
# VALIDADORES DE MONTOS/PRESUPUESTOS
# ============================================

def validate_positive_amount(value):
    """
    Valida que un monto sea positivo.
    """
    if value is None:
        return
    
    try:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise ValidationError(
                _("El monto debe ser mayor a cero."),
                code='non_positive_amount'
            )
    except (InvalidOperation, ValueError):
        raise ValidationError(
            _("Introduce un monto válido."),
            code='invalid_amount'
        )


def validate_reasonable_amount(value, max_amount=1000000000):
    """
    Valida que un monto esté dentro de un rango razonable.
    Por defecto: máximo 1,000,000,000 (mil millones)
    """
    if value is None:
        return
    
    try:
        decimal_value = Decimal(str(value))
        if decimal_value > max_amount:
            raise ValidationError(
                _(f"El monto no puede exceder ${max_amount:,.2f}"),
                code='amount_too_large'
            )
    except (InvalidOperation, ValueError):
        raise ValidationError(
            _("Introduce un monto válido."),
            code='invalid_amount'
        )


def validate_budget_amount(value):
    """
    Validador específico para presupuestos de proyectos.
    """
    validate_positive_amount(value)
    validate_reasonable_amount(value, max_amount=Decimal('1000000000'))  # 1 mil millones


def validate_payment_amount(value):
    """
    Validador específico para pagos.
    """
    validate_positive_amount(value)
    validate_reasonable_amount(value, max_amount=Decimal('100000000'))  # 100 millones por pago


# ============================================
# VALIDADORES DE ARCHIVOS
# ============================================

def validate_file_size(file, max_mb=10):
    """
    Valida el tamaño máximo de un archivo.
    """
    if not file:
        return
    
    max_bytes = max_mb * 1024 * 1024
    
    if file.size > max_bytes:
        raise ValidationError(
            _(f"El archivo no puede exceder {max_mb} MB. "
              f"Tamaño actual: {file.size / (1024*1024):.2f} MB"),
            code='file_too_large'
        )


def validate_file_extension(file, allowed_extensions):
    """
    Valida que la extensión del archivo esté permitida.
    
    Args:
        file: El archivo a validar
        allowed_extensions: Lista de extensiones permitidas (ej: ['.pdf', '.jpg'])
    """
    if not file:
        return
    
    import os
    ext = os.path.splitext(file.name)[1].lower()
    
    if ext not in [e.lower() for e in allowed_extensions]:
        raise ValidationError(
            _(f"Tipo de archivo no permitido. "
              f"Extensiones permitidas: {', '.join(allowed_extensions)}"),
            code='invalid_file_type'
        )


def validate_image_file(file):
    """
    Validador específico para archivos de imagen.
    """
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    validate_file_extension(file, allowed_extensions)
    validate_file_size(file, max_mb=5)  # 5 MB para imágenes


def validate_document_file(file):
    """
    Validador específico para archivos de documentos.
    """
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls']
    validate_file_extension(file, allowed_extensions)
    validate_file_size(file, max_mb=10)  # 10 MB para documentos


def validate_receipt_file(file):
    """
    Validador específico para comprobantes de pago.
    """
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    validate_file_extension(file, allowed_extensions)
    validate_file_size(file, max_mb=5)


# ============================================
# VALIDADORES DE SANITIZACIÓN
# ============================================

def validate_no_html_tags(value):
    """
    Valida que un campo de texto no contenga etiquetas HTML.
    Prevención básica de XSS.
    """
    if not value:
        return
    
    # Detectar etiquetas HTML comunes
    if re.search(r'<[^>]+>', value):
        raise ValidationError(
            _("No se permiten etiquetas HTML en este campo."),
            code='html_not_allowed'
        )


def validate_safe_text(value):
    """
    Valida que el texto no contenga caracteres potencialmente peligrosos.
    """
    if not value:
        return
    
    # Detectar scripts y código potencialmente peligroso
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onclick=',
        r'onload=',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                _("El texto contiene contenido no permitido."),
                code='unsafe_content'
            )


# ============================================
# VALIDADORES DE UNICIDAD
# ============================================

def validate_unique_in_queryset(value, queryset, field_name, instance=None):
    """
    Valida que un valor sea único en un queryset.
    
    Args:
        value: El valor a validar
        queryset: El queryset donde buscar
        field_name: Nombre del campo a mostrar en el error
        instance: Instancia actual (para excluir en edición)
    """
    lookup = {field_name: value}
    qs = queryset.filter(**lookup)
    
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    
    if qs.exists():
        raise ValidationError(
            _(f"Ya existe un registro con este {field_name}."),
            code='duplicate_value'
        )


# ============================================
# VALIDADORES DE ORDEN/POSICIÓN
# ============================================

def validate_positive_integer(value):
    """
    Valida que un número entero sea positivo.
    """
    if value is not None and value <= 0:
        raise ValidationError(
            _("El valor debe ser un número positivo."),
            code='non_positive_integer'
        )


def validate_order_number(value, max_order=1000):
    """
    Valida un número de orden (para fases, tareas, etc.)
    """
    validate_positive_integer(value)
    
    if value and value > max_order:
        raise ValidationError(
            _(f"El orden no puede ser mayor a {max_order}."),
            code='order_too_large'
        )


# ============================================
# VALIDADORES DE CONTRASEÑA (CON TRADUCCIONES)
# ============================================

def validate_password_spanish(password, user=None):
    """
    Valida contraseña usando los validadores de Django,
    pero traduce los mensajes de error al español.
    
    Args:
        password: La contraseña a validar
        user: El usuario (opcional, para validaciones personalizadas)
    
    Raises:
        ValidationError: Si la contraseña no cumple los requisitos
    """
    # Traducciones de mensajes de Django al español
    translations_map = {
        'This password is too short. It must contain at least 8 characters.': 
            'La contraseña es demasiado corta. Debe contener al menos 8 caracteres.',
        'This password is entirely numeric.':
            'La contraseña no puede ser completamente numérica.',
        'Esta contraseña es completamente numérica.':
            'La contraseña no puede ser completamente numérica.',
        'This password is too common.':
            'Esta contraseña es demasiado común. Elige una más segura.',
        'The password is too similar to the username.':
            'La contraseña es demasiado similar al nombre de usuario.',
        'The password is too similar to the user email.':
            'La contraseña es demasiado similar a tu correo electrónico.',
        'Your password must contain at least 8 characters.':
            'Tu contraseña debe contener al menos 8 caracteres.',
        'This password is not commonly used.':
            'Esta contraseña es muy común. Por favor, elige una más segura.',
    }
    
    try:
        # Usar el validador de Django
        django_validate_password(password, user=user)
    except ValidationError as e:
        # Traducir los mensajes de error
        translated_messages = []
        
        if hasattr(e, 'messages'):
            # Si es una lista de mensajes
            for message in e.messages:
                translated = translations_map.get(str(message), str(message))
                translated_messages.append(translated)
        elif hasattr(e, 'message'):
            # Si es un solo mensaje
            message = e.message
            translated = translations_map.get(str(message), str(message))
            translated_messages.append(translated)
        else:
            # En cualquier otro caso
            translated_messages.append(str(e))
        
        # Re-lanzar con mensajes traducidos
        raise ValidationError(translated_messages, code=getattr(e, 'code', 'invalid_password'))
