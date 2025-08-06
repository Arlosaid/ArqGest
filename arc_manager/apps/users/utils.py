import string
import random
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

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
    try:
        # Obtener el site_name de manera segura
        site_name = getattr(settings, 'SITE_NAME', 'ARC Manager')
        
        # Construir la URL de login
        if request:
            login_url = request.build_absolute_uri('/accounts/login/')
        else:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            login_url = f"{base_url}/accounts/login/"
        
        # Preparar el contexto para el template
        context = {
            'user': user,
            'password': password,
            'site_name': site_name,
            'login_url': login_url
        }
        
        # Renderizar los templates HTML y texto plano
        html_message = render_to_string('users/emails/new_user_credentials.html', context)
        
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
        
        # Usar EmailMultiAlternatives para enviar tanto HTML como texto plano
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=to_emails
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Email de credenciales enviado a {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email a {user.email}: {str(e)}")
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
 