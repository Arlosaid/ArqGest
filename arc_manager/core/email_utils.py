"""
Utilidades para envío de emails usando Resend API
Railway bloquea SMTP, por eso usamos la API directamente
"""
import os
import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)


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
    Envía un email usando la API de Resend (simple y directo)
    
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
            logger.error(f"Invalid configuration: {error_message}")
            return None
        
        # Configurar API key
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        resend.api_key = api_key
        
        # Preparar datos del email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'adroal08@gmail.com')
        
        email_data = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Agregar texto plano si se proporciona
        if text_content:
            email_data["text"] = text_content
            
        # Agregar reply-to si está configurado
        reply_to = getattr(settings, 'REPLY_TO_EMAIL', None)
        if reply_to:
            email_data["reply_to"] = [reply_to]
        
        # Enviar usando Resend API
        response = resend.Emails.send(email_data)
        
        # Resend retorna un dict con 'id' cuando es exitoso
        if response and isinstance(response, dict) and 'id' in response:
            logger.info("Email sent successfully")
            return response
        elif response:
            logger.info("Email sent")
            return response
        else:
            logger.error("Error: invalid response")
            return None
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        
        # Solo mostrar código de error si es ResendError
        if hasattr(e, 'code'):
            logger.error(f"Código: {e.code}")
        
        return None


def send_credentials_email(user_email, username, password):
    """
    Envía email con credenciales de usuario (función específica para tu caso)
    """
    subject = "Tus credenciales de acceso - ARC Manager"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">¡Bienvenido a ARC Manager!</h2>
            
            <p>Hemos creado tu cuenta en ARC Manager. Aquí tienes tus credenciales de acceso:</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Usuario:</strong> {username}</p>
                <p><strong>Contraseña:</strong> {password}</p>
            </div>
            
            <p>Por favor, inicia sesión y cambia tu contraseña por una de tu preferencia.</p>
            
            <p style="margin-top: 30px;">
                Saludos,<br>
                <strong>Equipo ARC Manager</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    ¡Bienvenido a ARC Manager!
    
    Hemos creado tu cuenta en ARC Manager. Aquí tienes tus credenciales de acceso:
    
    Usuario: {username}
    Contraseña: {password}
    
    Por favor, inicia sesión y cambia tu contraseña por una de tu preferencia.
    
    Saludos,
    Equipo ARC Manager
    """
    
    return send_resend_email(user_email, subject, html_content, text_content)


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
