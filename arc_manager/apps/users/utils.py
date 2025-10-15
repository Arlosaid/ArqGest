"""
Utilidades de usuarios simplificadas para Railway + Resend
Sin threads complejos, sin SMTP, solo API simple de Resend
"""
import logging
import string
import random
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_random_password(length=12):
    """
    🔐 Genera una contraseña aleatoria segura
    """
    # Definir los conjuntos de caracteres (sin caracteres confusos)
    uppercase = 'ABCDEFGHIJKLMNPQRSTUVWXYZ'  # Sin O
    lowercase = 'abcdefghijkmnpqrstuvwxyz'   # Sin l, o
    digits = '23456789'                       # Sin 0, 1
    symbols = '@#$%&*+'                      # Símbolos seguros
    
    # Asegurar al menos un carácter de cada tipo
    password = [
        random.choice(uppercase),
        random.choice(lowercase), 
        random.choice(digits),
        random.choice(symbols)
    ]
    
    # Completar con caracteres aleatorios
    all_chars = uppercase + lowercase + digits + symbols
    for _ in range(length - 4):
        password.append(random.choice(all_chars))
    
    # Mezclar
    random.shuffle(password)
    
    return ''.join(password)


def send_user_credentials_email(user_email, password, username, subject=None, user_obj=None):
    """
    Función principal para enviar credenciales de usuario (TEMPORALMENTE DESHABILITADO)
    """
    # TODO: Reactivar cuando tengas dominio propio
    # Validaciones básicas
    if not user_email or '@' not in user_email:
        logger.error(f"Invalid email: {user_email}")
        return False
        
    if not password or not username:
        logger.error(f"Missing data for {user_email}")
        return False
    
    # TEMPORALMENTE DESHABILITADO - No enviar emails hasta tener dominio
    logger.info("Email disabled - use 'Generate and show passwords' in admin")
    
    # Simular éxito para no romper el flujo
    return True
    
    # Código original comentado:
    # from core.email_utils import send_credentials_email
    # try:
    #     result = send_credentials_email(user_email, username, password)
    #     if result:
    #         logger.info(f"✅ [EMAIL] Credenciales enviadas exitosamente a {user_email}")
    #         return True
    #     else:
    #         logger.error(f"❌ [EMAIL] Error enviando credenciales a {user_email}")
    #         return False
    # except Exception as e:
    #     logger.error(f"❌ [EMAIL] Error enviando credenciales a {user_email}: {e}")
    #     return False


def send_welcome_email(user_email, username, subject=None):
    """
    Función para enviar email de bienvenida (SIMPLE)
    """
    logger.info(f"[EMAIL] Sending welcome email to {user_email}")
    
    # Validaciones
    if not user_email or '@' not in user_email:
        logger.error(f"[EMAIL] Invalid email: {user_email}")
        return False
    
    from core.email_utils import send_resend_email
    
    subject = subject or f"¡Bienvenido a {getattr(settings, 'SITE_NAME', 'ARC Manager')}!"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">¡Bienvenido a ARC Manager!</h2>
            
            <p>Hola <strong>{username}</strong>,</p>
            
            <p>Tu cuenta ha sido creada exitosamente. Ya puedes acceder al sistema con tus credenciales.</p>
            
            <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
            
            <p style="margin-top: 30px;">
                Saludos,<br>
                <strong>Equipo ARC Manager</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        result = send_resend_email(user_email, subject, html_content)
        if result:
            logger.info(f"[EMAIL] Welcome email sent to {user_email}")
            return True
        else:
            logger.error(f"[EMAIL] Error sending welcome email to {user_email}")
            return False
    except Exception as e:
        logger.error(f"[EMAIL] Error sending welcome email to {user_email}: {e}")
        return False


def test_email_configuration():
    """
    Test simple de configuración de email
    """
    logger.info("[EMAIL] Testing email configuration...")
    
    # Verificar que tenemos API key de Resend
    api_key = getattr(settings, 'RESEND_API_KEY', None)
    if not api_key:
        logger.error("[EMAIL] RESEND_API_KEY not configured")
        return False
    
    logger.info("[EMAIL] RESEND_API_KEY configured")
    logger.info("[EMAIL] Basic configuration OK")
    return True


def send_new_user_email(user, password, request=None, background=True):
    """
    Envía email de credenciales a nuevo usuario (SIMPLE)
    """
    # Usar el nombre completo o email como username para el email
    username_for_email = user.full_name or user.email
    
    return send_user_credentials_email(
        user_email=user.email,
        password=password,
        username=username_for_email,
        user_obj=user
    )


def send_welcome_reminder_email(user, request=None):
    """
    🎉 Envía recordatorio de bienvenida (SIMPLE)
    """
    # Usar el nombre completo o email como username para el email
    username_for_email = user.full_name or user.email
    
    return send_welcome_email(
        user_email=user.email,
        username=username_for_email
    )
