import string
import random
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)

def generate_random_password(length=12):
    """
    Genera una contraseña aleatoria segura con la longitud especificada.
    La contraseña incluye mayúsculas, minúsculas, números y caracteres especiales.
    """
    # Definir los conjuntos de caracteres
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    # Caracteres especiales más seguros y fáciles de usar
    special = '!@#$%&*'
    
    # Asegurar al menos un carácter de cada tipo
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Completar el resto de la contraseña con caracteres aleatorios
    all_chars = lowercase + uppercase + digits + special
    password.extend(random.choice(all_chars) for _ in range(length - 4))
    
    # Mezclar los caracteres
    random.shuffle(password)
    
    # Convertir la lista a string
    return ''.join(password)

def send_new_user_email(user, password, request=None):
    """
    Envía un email al nuevo usuario con sus credenciales de acceso.
    Retorna True si el email se envió correctamente, False en caso contrario.
    """
    import time
    from django.core.mail import get_connection
    
    logger.info(f"🚀 Iniciando envío de credenciales para {user.email}")
    
    try:
        # Verificar configuración de email antes de proceder
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'No configurado')
        email_host = getattr(settings, 'EMAIL_HOST', 'No configurado')
        default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')
        
        logger.info(f"📧 Configuración EMAIL_BACKEND: {email_backend}")
        logger.info(f"📧 Configuración EMAIL_HOST: {email_host}")
        logger.info(f"📧 Configuración DEFAULT_FROM_EMAIL: {default_from_email}")
        
        # Obtener el site_name de manera segura
        site_name = getattr(settings, 'SITE_NAME', 'ARC Manager')
        
        # Construir la URL de login
        if request:
            login_url = request.build_absolute_uri('/accounts/login/')
        else:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            login_url = f"{base_url}/accounts/login/"
        
        logger.info(f"🔗 URL de login generada: {login_url}")
        
        # Preparar el contexto para el template
        context = {
            'user': user,
            'password': password,
            'site_name': site_name,
            'login_url': login_url
        }
        
        logger.info(f"📝 Renderizando template HTML...")
        # Renderizar los templates HTML y texto plano
        html_message = render_to_string('users/emails/new_user_credentials.html', context)
        logger.info(f"✅ Template HTML renderizado correctamente")
        
        # Determinar el nombre para mostrar
        display_name = f"{user.first_name} {user.last_name}".strip()
        if not display_name:
            display_name = user.username or user.email
        
        # Crear también una versión en texto plano para compatibilidad
        text_message = f"""
¡Bienvenido a {site_name}!

Hola {display_name},

Se ha creado una cuenta para ti en {site_name}. A continuación encontrarás tus credenciales de acceso:

📧 Correo electrónico: {user.email}
👤 Usuario: {user.username or user.email}
🔒 Contraseña: {password}

🚀 Acceder al Sistema: {login_url}

💡 Recomendación: Por tu seguridad, te recomendamos cambiar esta contraseña por una de tu elección cuando ingreses al sistema por primera vez.

🛡️ Consejos de Seguridad:
- Considera cambiar tu contraseña por una de tu preferencia
- Usa una contraseña fuerte que incluya mayúsculas, minúsculas, números y símbolos
- No compartas tus credenciales con nadie
- Cierra sesión cuando termines de usar el sistema
- Si olvidas tu contraseña, puedes restablecerla desde la página de login

{f"🏢 Organización: {user.organization.name}" if user.organization else ""}

Si tienes alguna pregunta o problema para acceder al sistema, contacta a tu administrador.

Este mensaje fue generado automáticamente, por favor no respondas a este email.

{site_name} - Sistema de Gestión
        """
        
        # Crear email con contenido HTML y texto plano
        subject = f'Bienvenido a {site_name} - Tus credenciales de acceso'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
        to_emails = [user.email]
        

        # Logging detallado para debugging
        logger.info(f"🔗 URL de login generada: {login_url}")
        logger.info(f"📝 Renderizando template HTML...")
        logger.info(f"✅ Template HTML renderizado correctamente")
        logger.info(f"📬 Preparando email: {subject}")
        logger.info(f"📤 De: {from_email} -> Para: {user.email}")
        
        # Usar EmailMultiAlternatives para enviar tanto HTML como texto plano
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=to_emails
        )
        email.attach_alternative(html_message, "text/html")
        
        logger.info(f"🔌 Estableciendo conexión SMTP...")
        logger.info(f"📨 Enviando email...")
        
        # Enviar con timeout personalizado
        import socket
        import time
        
        start_time = time.time()
        try:
            # Configurar timeout de socket específicamente para el envío
            default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(30)  # 30 segundos timeout
            
            email.send()
            
            # Restaurar timeout original
            socket.setdefaulttimeout(default_timeout)
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Email enviado exitosamente en {elapsed_time:.2f}s a {user.email}")
            return True
            
        except socket.timeout:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Timeout enviando email a {user.email} ({elapsed_time:.0f}s)")
            return False
        except Exception as smtp_error:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Error SMTP enviando email a {user.email} ({elapsed_time:.0f}s): {str(smtp_error)}")
            return False
        finally:
            # Asegurar que se restaure el timeout
            socket.setdefaulttimeout(default_timeout)

        
    except Exception as e:
        logger.error(f"❌ Error general enviando email a {user.email}: {str(e)}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        
        # Log adicional para debugging
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        
        return False

def send_welcome_reminder_email(user, request=None):
    """
    Envía un email de recordatorio de bienvenida a un usuario existente.
    """
    try:
        site_name = getattr(settings, 'SITE_NAME', 'ARC Manager')
        if request:
            login_url = request.build_absolute_uri(reverse('accounts:login'))
        else:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            login_url = f"{base_url}{reverse('accounts:login')}"

        context = {
            'user': user,
            'site_name': site_name,
            'login_url': login_url
        }
        
        html_message = render_to_string('users/emails/welcome_reminder.html', context)
        text_message = f"Hola {user.full_name},\n\nEste es un recordatorio de que tienes una cuenta en {site_name}.\nPuedes acceder aquí: {login_url}\n\nEl equipo de {site_name}"
        
        subject = f'Recordatorio de tu cuenta en {site_name}'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
        
        email = EmailMultiAlternatives(subject, text_message, from_email, [user.email])
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Email de recordatorio de bienvenida enviado a {user.email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email de recordatorio a {user.email}: {str(e)}")
        return False
 