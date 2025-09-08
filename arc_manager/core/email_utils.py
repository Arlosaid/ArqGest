"""
Utilidades para envío de emails usando Resend API
Railway bloquea SMTP, por eso usamos la API directamente
"""
import os
import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)


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
        # Configurar API key
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        if not api_key:
            logger.error("❌ RESEND_API_KEY no está configurado")
            return None
            
        resend.api_key = api_key
        
        # Preparar datos del email
        email_data = {
            "from": getattr(settings, 'DEFAULT_FROM_EMAIL', 'ARC Manager <onboarding@resend.dev>'),
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
        logger.info(f"📧 Enviando email a {to_email} - {subject}")
        response = resend.Emails.send(email_data)
        
        logger.info(f"✅ Email enviado exitosamente - ID: {response.get('id', 'N/A')}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error enviando email a {to_email}: {e}")
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
