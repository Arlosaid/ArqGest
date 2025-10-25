"""
Utilidades para envío de emails usando Resend API
Railway bloquea SMTP, por eso usamos la API directamente
Implementa logging estructurado con trazabilidad completa
"""
import os
import logging
import resend
from django.conf import settings
from core.error_codes import EmailErrorCodes
from core.structured_logging import log_error, log_info

logger = logging.getLogger('core.email')


def get_site_protocol_and_domain():
    """
    Obtiene el protocolo y dominio del sitio para usar en emails
    
    Returns:
        tuple: (protocol, domain)
    """
    # Intentar obtener SITE_URL de diferentes fuentes
    site_url = getattr(settings, 'SITE_URL', None)
    
    # Si no hay SITE_URL configurado, intentar obtenerlo de otras fuentes
    if not site_url:
        # En producción, intentar obtener de Railway
        if hasattr(settings, 'RAILWAY_STATIC_URL'):
            site_url = settings.RAILWAY_STATIC_URL
        # Fallback a localhost para desarrollo
        else:
            site_url = 'http://localhost:8000'
    
    # Log para debugging
    logger.info(f"[EMAIL] Using SITE_URL: {site_url}")
    
    if site_url.startswith('https://'):
        protocol = 'https'
        domain = site_url.replace('https://', '').rstrip('/')
    elif site_url.startswith('http://'):
        protocol = 'http'
        domain = site_url.replace('http://', '').rstrip('/')
    else:
        # Si no tiene protocolo, asumir https en producción
        protocol = 'https' if not settings.DEBUG else 'http'
        domain = site_url.rstrip('/')
    
    logger.info(f"[EMAIL] Resolved protocol: {protocol}, domain: {domain}")
    return protocol, domain


def validate_resend_config():
    """
    Valida la configuración de Resend antes de enviar emails
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        
        if not api_key:
            return False, "RESEND_API_KEY no está configurado en las variables de entorno"
        
        if not api_key.startswith('re_'):
            return False, f"API Key inválida - debe comenzar con 're_', actual: {api_key[:10]}..."
        
        if len(api_key) < 20:
            return False, f"API Key muy corta - longitud actual: {len(api_key)}"
        
        # Verificar email origen
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not from_email:
            return False, "DEFAULT_FROM_EMAIL no está configurado"
        
        if '@resend.dev' not in from_email and '@' not in from_email:
            return False, f"Email origen inválido: {from_email}"
        
        return True, "Configuración válida"
        
    except Exception as e:
        return False, f"Error validando configuración: {e}"


def send_resend_email(to_email, subject, html_content, text_content=None):
    """
    Envía un email usando la API de Resend con logging estructurado completo
    
    Args:
        to_email (str): Email del destinatario
        subject (str): Asunto del email
        html_content (str): Contenido HTML del email
        text_content (str, optional): Contenido de texto plano
    
    Returns:
        dict: Respuesta de Resend API o None si hay error
    """
    try:
        # Validar configuración primero
        is_valid, error_message = validate_resend_config()
        if not is_valid:
            log_error(
                event='email_config_validation',
                error_code=EmailErrorCodes.EMAIL_CONFIG_BACKEND_ERROR,
                validation_error=error_message,
                to_email=to_email,
                logger_name='core.email'
            )
            return None
        
        # Configurar API key
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        resend.api_key = api_key
        
        # Preparar datos del email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ArqGest <noreply@arqgest.com>')
        
        # Si no hay texto plano, generar uno básico desde el HTML
        if not text_content:
            # Extraer texto básico del HTML para clientes que no soportan HTML
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)  # Remover tags HTML
            text_content = re.sub(r'\s+', ' ', text_content).strip()  # Normalizar espacios
        
        email_data = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
            "text": text_content  # SIEMPRE incluir texto plano
        }
        
        # Agregar reply-to si está configurado
        reply_to = getattr(settings, 'REPLY_TO_EMAIL', None)
        if reply_to:
            email_data["reply_to"] = [reply_to]
        
        # Log inicio de envío
        log_info(
            event='email_send_start',
            to_email=to_email,
            sender=from_email,
            subject=subject[:50],
            has_html=True,
            has_text=text_content is not None,
            provider='Resend',
            logger_name='core.email'
        )
        
        # Enviar usando Resend API
        response = resend.Emails.send(email_data)
        
        # Resend retorna un dict con 'id' cuando es exitoso
        if response and isinstance(response, dict) and 'id' in response:
            log_info(
                event='email_send_success',
                error_code=EmailErrorCodes.EMAIL_SEND_SUCCESS,
                email_id=response['id'],
                to_email=to_email,
                sender=from_email,
                subject=subject[:50],
                provider='Resend',
                logger_name='core.email'
            )
            return response
        elif response:
            log_error(
                event='email_send_warning',
                error_code=EmailErrorCodes.EMAIL_SEND_API_ERROR,
                to_email=to_email,
                sender=from_email,
                subject=subject[:50],
                response=str(response)[:100],
                reason='Respuesta sin ID de Resend',
                logger_name='core.email'
            )
            return response
        else:
            log_error(
                event='email_send_error',
                error_code=EmailErrorCodes.EMAIL_SEND_FAILED,
                to_email=to_email,
                sender=from_email,
                subject=subject[:50],
                reason='Respuesta vacía de Resend API',
                logger_name='core.email'
            )
            return None
        
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        
        # Determinar código de error específico
        if 'rate' in error_message.lower() or 'limit' in error_message.lower():
            error_code = EmailErrorCodes.EMAIL_SEND_RATE_LIMIT
        elif 'quota' in error_message.lower():
            error_code = EmailErrorCodes.EMAIL_SEND_QUOTA_EXCEEDED
        elif 'invalid' in error_message.lower() and 'key' in error_message.lower():
            error_code = EmailErrorCodes.EMAIL_CONFIG_API_KEY_INVALID
        else:
            error_code = EmailErrorCodes.EMAIL_SEND_FAILED
        
        log_error(
            event='email_send_error',
            error_code=error_code,
            to_email=to_email,
            subject=subject[:50],
            error_type=error_type,
            error_message=error_message[:200],
            provider='Resend',
            has_code=hasattr(e, 'code'),
            logger_name='core.email'
        )
        
        return None


def send_credentials_email(user_email, username, password):
    """
    Envía email con credenciales de usuario usando el template mejorado
    """
    from django.template.loader import render_to_string
    
    # NO logear nada en flujo exitoso - solo errores
    site_name = getattr(settings, 'SITE_NAME', 'ArqGest')
    subject = f"¡Bienvenido a {site_name}!"
    protocol, domain = get_site_protocol_and_domain()
    
    context = {
        'user': {'email': user_email, 'first_name': '', 'last_name': ''},
        'password': password,
        'site_name': site_name,
        'login_url': f"{protocol}://{domain}/accounts/login/",
        'protocol': protocol,
        'domain': domain
    }
    
    # NUNCA logear context porque contiene password
    
    try:
        # Renderizar templates sin logging innecesario
        html_content = render_to_string('users/emails/new_user_credentials.html', context)
        text_content = render_to_string('users/emails/new_user_credentials.txt', context)
        
        # Enviar email - el backend ya loguea si falla
        result = send_resend_email(user_email, subject, html_content, text_content)
        
        return result
        
    except Exception as e:
        # Solo logear errores, sin traceback completo
        logger.error(f"[EMAIL] Error sending credentials email: {str(e)}")
        return None






def test_resend_connection():
    """
    Función para probar la conexión con Resend API
    
    Returns:
        dict: Resultado del test con información detallada
    """
    logger.info("Testing Resend connection...")
    
    # Validar configuración
    is_valid, error_message = validate_resend_config()
    if not is_valid:
        return {
            'success': False,
            'error': 'Configuración inválida',
            'details': error_message
        }
    
    try:
        # Configurar Resend
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        resend.api_key = api_key
        
        # Intentar enviar un email de test muy simple
        test_email = "test@example.com"  # Email que no existe, solo para test de API
        
        email_data = {
            "from": getattr(settings, 'DEFAULT_FROM_EMAIL', 'ARC Manager <onboarding@resend.dev>'),
            "to": [test_email],
            "subject": "Test de conexión - ARC Manager",
            "html": "<p>Test de conexión</p>"
        }
        
        logger.info("🧪 Intentando conectar con Resend API...")
        
        # Esto debería fallar por el email inválido, pero nos dará información sobre la API
        response = resend.Emails.send(email_data)
        
        return {
            'success': True,
            'message': 'Conexión exitosa',
            'response': response
        }
        
    except Exception as e:
        # Analizar el tipo de error
        error_info = {
            'success': False,
            'error_type': str(type(e)),
            'error_message': str(e),
            'api_key_format': f"{api_key[:10]}..." if api_key else "NONE"
        }
        
        if hasattr(e, 'code'):
            error_info['resend_code'] = e.code
        if hasattr(e, 'message'):
            error_info['resend_message'] = e.message
        if hasattr(e, 'error_type'):
            error_info['resend_error_type'] = e.error_type
            
        logger.error(f"🧪 Test falló: {error_info}")
        return error_info
