"""
Utilidades de logging estructurado para toda la aplicación.
Facilita el logging con contexto JSON en lugar de strings planos.

Uso:
    from core.structured_logging import log_error, log_warning, log_info, log_business_event
    
    # En lugar de:
    logger.error(f"Error al guardar usuario {email}: {error}")
    
    # Usar:
    log_error(
        event="user_save_failed",
        error_code="USR001",
        user_email=email,  # Se anonimizará automáticamente
        error_message=str(error)
    )
"""
import logging
from typing import Any, Dict, Optional
from .logging_filters import get_request_id, get_user_context


def _get_logger(name: str = 'apps') -> logging.Logger:
    """Obtiene un logger con el nombre especificado"""
    return logging.getLogger(name)


def _add_context(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Agrega contexto automático de request_id y user_context a los logs.
    """
    context = extra or {}
    
    # Agregar request_id si existe
    request_id = get_request_id()
    if request_id:
        context['request_id'] = request_id
    
    # Agregar user context si existe
    user_ctx = get_user_context()
    if user_ctx.get('user_id'):
        context['user_id'] = user_ctx['user_id']
    if user_ctx.get('organization_id'):
        context['organization_id'] = user_ctx['organization_id']
    
    return context


def log_error(
    event: str,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    logger_name: str = 'apps',
    **kwargs
) -> None:
    """
    Loggea un error con formato estructurado.
    
    Args:
        event: Nombre del evento (ej: "user_save_failed", "payment_processing_error")
        error_code: Código de error único (ej: "USR001", "PAY500")
        error_message: Mensaje de error legible
        logger_name: Nombre del logger a usar
        **kwargs: Campos adicionales para el contexto
    
    Ejemplo:
        log_error(
            event="subscription_creation_failed",
            error_code="SUB001",
            error_message="Plan no encontrado",
            plan_id=123,
            organization_id=456
        )
    """
    logger = _get_logger(logger_name)
    
    # Construir mensaje estructurado
    data = {
        'event': event,
    }
    
    if error_code:
        data['error_code'] = error_code
    if error_message:
        data['error_message'] = error_message
    
    # Agregar campos adicionales
    data.update(kwargs)
    
    # Crear mensaje CLARO Y DIRECTO con toda la información
    msg_parts = []
    
    # Siempre empezar con el evento en formato legible
    msg_parts.append(f"❌ {event.replace('_', ' ').upper()}")
    
    # Agregar código de error si existe
    if error_code:
        msg_parts.append(f"[{error_code}]")
    
    # Agregar mensaje de error (LO MÁS IMPORTANTE)
    if error_message:
        msg_parts.append(f"- {error_message}")
    
    # Agregar contexto adicional relevante
    context_parts = []
    for key, value in kwargs.items():
        if key not in ['event', 'error_code', 'error_message']:
            # Solo agregar campos importantes al mensaje principal
            if key in ['user_email', 'user_id', 'organization_id', 'file_name', 'project_id']:
                context_parts.append(f"{key}={value}")
    
    if context_parts:
        msg_parts.append(f"| {' | '.join(context_parts)}")
    
    msg = ' '.join(msg_parts)
    
    # Loggear con contexto adicional
    logger.error(msg, extra=_add_context(data))


def log_warning(
    event: str,
    message: Optional[str] = None,
    logger_name: str = 'apps',
    **kwargs
) -> None:
    """
    Loggea un warning con formato estructurado.
    
    Args:
        event: Nombre del evento
        message: Mensaje descriptivo
        logger_name: Nombre del logger a usar
        **kwargs: Campos adicionales
    
    Ejemplo:
        log_warning(
            event="subscription_near_expiry",
            message="Suscripción expira en 2 días",
            subscription_id=123,
            days_remaining=2
        )
    """
    logger = _get_logger(logger_name)
    
    data = {'event': event}
    if message:
        data['message'] = message
    data.update(kwargs)
    
    # Mensaje CLARO Y DIRECTO
    msg = f"⚠️ {event.replace('_', ' ').upper()}"
    if message:
        msg += f" - {message}"
    
    logger.warning(msg, extra=_add_context(data))


def log_info(
    event: str,
    message: Optional[str] = None,
    logger_name: str = 'apps',
    **kwargs
) -> None:
    """
    Loggea información con formato estructurado.
    
    Args:
        event: Nombre del evento
        message: Mensaje descriptivo
        logger_name: Nombre del logger a usar
        **kwargs: Campos adicionales
    
    Ejemplo:
        log_info(
            event="subscription_created",
            message="Nueva suscripción creada exitosamente",
            subscription_id=123,
            plan_name="Premium"
        )
    """
    logger = _get_logger(logger_name)
    
    data = {'event': event}
    if message:
        data['message'] = message
    data.update(kwargs)
    
    # Mensaje CLARO Y DIRECTO
    msg = f"ℹ️ {event.replace('_', ' ').title()}"
    if message:
        msg += f" - {message}"
    
    logger.info(msg, extra=_add_context(data))


def log_business_event(
    event: str,
    action: str,
    entity_type: str,
    entity_id: Any,
    outcome: str = "success",
    logger_name: str = 'apps',
    **kwargs
) -> None:
    """
    Loggea eventos de negocio importantes (nivel INFO).
    Útil para auditoría y análisis de negocio.
    
    Args:
        event: Nombre del evento de negocio
        action: Acción realizada (created, updated, deleted, etc.)
        entity_type: Tipo de entidad (subscription, organization, user, etc.)
        entity_id: ID de la entidad
        outcome: Resultado (success, failed, etc.)
        logger_name: Nombre del logger
        **kwargs: Campos adicionales
    
    Ejemplo:
        log_business_event(
            event="organization_created",
            action="created",
            entity_type="organization",
            entity_id=123,
            outcome="success",
            organization_name="ACME Corp",
            created_by_user_id=456
        )
    """
    logger = _get_logger(logger_name)
    
    data = {
        'event': event,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'outcome': outcome,
    }
    data.update(kwargs)
    
    msg = f"[{event}] {action} {entity_type} {entity_id} - {outcome}"
    
    logger.info(msg, extra=_add_context(data))


def log_slow_operation(
    operation: str,
    duration_ms: float,
    threshold_ms: float = 2000,
    logger_name: str = 'apps',
    **kwargs
) -> None:
    """
    Loggea operaciones lentas para monitoreo de performance.
    
    Args:
        operation: Nombre de la operación
        duration_ms: Duración en milisegundos
        threshold_ms: Threshold de lentitud (default 2000ms)
        logger_name: Nombre del logger
        **kwargs: Campos adicionales
    
    Ejemplo:
        log_slow_operation(
            operation="file_upload",
            duration_ms=3500,
            file_size_mb=150,
            file_type="dwg"
        )
    """
    if duration_ms < threshold_ms:
        return  # No loggear si está dentro del threshold
    
    logger = _get_logger(logger_name)
    
    data = {
        'event': 'slow_operation',
        'operation': operation,
        'duration_ms': round(duration_ms, 2),
        'threshold_ms': threshold_ms,
    }
    data.update(kwargs)
    
    msg = f"[slow_operation] {operation} took {duration_ms:.0f}ms (threshold: {threshold_ms}ms)"
    
    logger.warning(msg, extra=_add_context(data))


def log_security_event(
    event: str,
    severity: str,
    ip_address: Optional[str] = None,
    logger_name: str = 'django.security',
    **kwargs
) -> None:
    """
    Loggea eventos de seguridad.
    
    Args:
        event: Nombre del evento de seguridad
        severity: Severidad (low, medium, high, critical)
        ip_address: IP del cliente (se anonimizará automáticamente)
        logger_name: Nombre del logger
        **kwargs: Campos adicionales
    
    Ejemplo:
        log_security_event(
            event="failed_login_attempt",
            severity="medium",
            ip_address=request.META['REMOTE_ADDR'],
            username="admin",
            attempts_count=5
        )
    """
    logger = _get_logger(logger_name)
    
    data = {
        'event': event,
        'severity': severity,
    }
    
    if ip_address:
        data['ip_address'] = ip_address  # El filtro lo anonimizará
    
    data.update(kwargs)
    
    msg = f"[security:{severity}] {event}"
    
    # Usar WARNING para medium/high, ERROR para critical
    if severity in ('critical', 'high'):
        logger.error(msg, extra=_add_context(data))
    else:
        logger.warning(msg, extra=_add_context(data))
