import threading
import logging
import time
import string
import random
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class EmailThread(threading.Thread):
    """
    🧵 Clase personalizada para envío de emails en background
    Optimizada para Railway + AWS SES desde México
    """
    def __init__(self, email_data):
        self.email_data = email_data
        threading.Thread.__init__(self, daemon=True)
        
    def run(self):
        """
        Ejecuta el envío del email
        """
        try:
            self._send_email()
        except Exception as e:
            logger.error(f"❌ [EMAIL_THREAD] Error crítico: {e}")
            
    def _send_email(self):
        """
        🚀 Lógica principal de envío optimizada
        """
        user_email = self.email_data['user_email']
        connection = None
        
        try:
            logger.info(f"🧵 [EMAIL] Iniciando envío para {user_email}")
            start_time = time.time()
            
            # Crear conexión optimizada para AWS SES
            connection = get_connection(
                backend=settings.EMAIL_BACKEND,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                timeout=20,  # Timeout específico para Railway
                fail_silently=False,
            )
            
            logger.info(f"🔌 [EMAIL] Estableciendo conexión SMTP con {settings.EMAIL_HOST}")
            
            # Abrir conexión
            connection.open()
            
            # Preparar email
            email = self._create_email(connection)
            
            # Enviar
            logger.info(f"📤 [EMAIL] Enviando email a {user_email}...")
            result = email.send()
            
            elapsed_time = time.time() - start_time
            
            if result:
                logger.info(f"✅ [EMAIL] ¡Éxito! Email enviado a {user_email} en {elapsed_time:.2f}s")
            else:
                logger.error(f"❌ [EMAIL] Fallo: send() retornó 0 para {user_email}")
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ [EMAIL] Error enviando a {user_email} después de {elapsed_time:.2f}s: {str(e)}")
            
            # Log detalles específicos del error
            if "authentication" in str(e).lower():
                logger.error("🔐 [EMAIL] Error de autenticación - Revisar AWS_SES_USER/PASS")
            elif "timeout" in str(e).lower():
                logger.error("⏱️ [EMAIL] Timeout - Conexión lenta, verifica región AWS")
            elif "connection" in str(e).lower():
                logger.error("🌐 [EMAIL] Error de conexión - Verificar EMAIL_HOST")
            elif "refused" in str(e).lower():
                logger.error("🚫 [EMAIL] Conexión rechazada - Verificar puerto y TLS")
                
        finally:
            # Cerrar conexión
            if connection:
                try:
                    connection.close()
                    logger.info(f"🔌 [EMAIL] Conexión cerrada para {user_email}")
                except:
                    pass
                    
    def _create_email(self, connection):
        """
        📧 Crea el objeto EmailMultiAlternatives optimizado
        """
        data = self.email_data
        
        # Renderizar templates (usando contexto compatible con tus templates existentes)
        # Crear objeto user-like para compatibilidad con template
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() or data['username']
        
        user_obj = type('User', (), {
            'email': data['user_email'],
            'username': data['username'],
            'first_name': first_name,
            'last_name': last_name,
            'organization': data.get('organization'),
            'full_name': full_name,
            'role_display': 'Usuario'
        })()
        
        context = {
            'user': user_obj,  # Objeto user para compatibilidad con template
            'username': data['username'],
            'password': data['password'],
            'login_url': f"{getattr(settings, 'SITE_URL', 'https://arcmanager-production.up.railway.app')}/accounts/login/",
            'site_name': getattr(settings, 'SITE_NAME', 'ARC Manager'),
            'user_email': data['user_email'],
            'generated_at': timezone.now()
        }
        
        logger.info(f"📝 [EMAIL] Renderizando templates para {data['user_email']}")
        
        # Renderizar contenido con fallback
        try:
            html_content = render_to_string('users/emails/new_user_credentials.html', context)
            logger.info(f"✅ [EMAIL] Template HTML renderizado correctamente")
            
            # Crear versión de texto plano a partir del contenido
            text_content = f"""
🎉 ¡Bienvenido a {context['site_name']}!

Hola {full_name},

Se ha creado una cuenta para ti en {context['site_name']}. A continuación encontrarás tus credenciales de acceso:

📧 Correo electrónico: {data['user_email']}
👤 Usuario: {data['username']}
🔒 Contraseña: {data['password']}

🚀 Acceder al Sistema: {context['login_url']}

💡 Recomendación: Por tu seguridad, te recomendamos cambiar esta contraseña por una de tu elección cuando ingreses al sistema por primera vez.

🛡️ Consejos de Seguridad:
- Considera cambiar tu contraseña por una de tu preferencia
- Usa una contraseña fuerte que incluya mayúsculas, minúsculas, números y símbolos
- No compartas tus credenciales con nadie
- Cierra sesión cuando termines de usar el sistema
- Si olvidas tu contraseña, puedes restablecerla desde la página de login

{f"🏢 Organización: {data.get('organization').name}" if data.get('organization') else ""}

Si tienes alguna pregunta o problema para acceder al sistema, contacta a tu administrador.

Este mensaje fue generado automáticamente el {context['generated_at'].strftime('%d/%m/%Y %H:%M')}, por favor no respondas a este email.

{context['site_name']} - Sistema de Gestión
            """
        except Exception as e:
            logger.error(f"❌ [EMAIL] Error renderizando templates: {e}")
            # Fallback a contenido simple
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">🎉 Bienvenido a {context['site_name']}</h2>
                <p>Hola <strong>{data['username']}</strong>,</p>
                <p>Se ha creado tu cuenta en {context['site_name']}. Aquí tienes tus credenciales:</p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>📧 Email:</strong> {data['user_email']}</p>
                    <p><strong>👤 Usuario:</strong> {data['username']}</p>
                    <p><strong>🔒 Contraseña:</strong> <code style="background: #e9ecef; padding: 2px 4px;">{data['password']}</code></p>
                </div>
                <p><a href="{context['login_url']}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🚀 Acceder al Sistema</a></p>
                <p><small>💡 Te recomendamos cambiar tu contraseña después del primer acceso.</small></p>
                <hr>
                <p><small>Este mensaje fue generado automáticamente. No respondas a este email.</small></p>
            </div>
            """
            text_content = f"""
            🎉 Bienvenido a {context['site_name']}
            
            Hola {data['username']},
            
            Se ha creado tu cuenta. Aquí tienes tus credenciales:
            
            📧 Email: {data['user_email']}
            👤 Usuario: {data['username']}
            🔒 Contraseña: {data['password']}
            
            🚀 Accede aquí: {context['login_url']}
            
            💡 Te recomendamos cambiar tu contraseña después del primer acceso.
            
            {context['site_name']} - Sistema de Gestión
            """
        
        # Crear email
        email = EmailMultiAlternatives(
            subject=data.get('subject', f'Bienvenido a {context["site_name"]} - Tus credenciales de acceso'),
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[data['user_email']],
            connection=connection
        )
        
        email.attach_alternative(html_content, "text/html")
        return email

def generate_random_password(length=12):
    """
    🔐 Genera una contraseña aleatoria segura
    """
    # Definir los conjuntos de caracteres (sin caracteres confusos)
    lowercase = 'abcdefghjkmnpqrstuvwxyz'  # Sin 'i', 'l', 'o'
    uppercase = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Sin 'I', 'O'
    digits = '23456789'  # Sin '0', '1'
    special = '!@#$%&*'
    
    # Asegurar al menos un carácter de cada tipo
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Completar el resto
    all_chars = lowercase + uppercase + digits + special
    password.extend(random.choice(all_chars) for _ in range(length - 4))
    
    # Mezclar
    random.shuffle(password)
    
    return ''.join(password)

def send_user_credentials_email(user_email, password, username, subject=None, user_obj=None):
    """
    🚀 Función principal para enviar credenciales de usuario (ASÍNCRONO)
    """
    logger.info(f"🚀 [EMAIL] Programando envío de credenciales para {user_email}")
    
    # Validaciones básicas
    if not user_email or '@' not in user_email:
        logger.error(f"❌ [EMAIL] Email inválido: {user_email}")
        return False
        
    if not password or not username:
        logger.error(f"❌ [EMAIL] Datos faltantes para {user_email}")
        return False
    
    # Preparar datos (incluyendo información adicional del usuario si está disponible)
    email_data = {
        'user_email': user_email,
        'password': password,
        'username': username,
        'subject': subject,
        'type': 'credentials'
    }
    
    # Si tenemos el objeto user completo, extraer más información
    if user_obj:
        email_data.update({
            'first_name': getattr(user_obj, 'first_name', ''),
            'last_name': getattr(user_obj, 'last_name', ''),
            'organization': getattr(user_obj, 'organization', None),
        })
    
    # Crear y ejecutar thread
    email_thread = EmailThread(email_data)
    email_thread.start()
    
    logger.info(f"🧵 [EMAIL] Thread iniciado para {user_email}")
    return True

def send_welcome_email(user_email, username, subject=None):
    """
    🎉 Función para enviar email de bienvenida (ASÍNCRONO)
    """
    logger.info(f"🎉 [EMAIL] Programando email de bienvenida para {user_email}")
    
    # Validaciones
    if not user_email or '@' not in user_email:
        logger.error(f"❌ [EMAIL] Email inválido: {user_email}")
        return False
    
    def _send_welcome():
        try:
            context = {
                'username': username,
                'login_url': f"{getattr(settings, 'SITE_URL', 'https://arcmanager-production.up.railway.app')}/accounts/login/",
                'site_name': getattr(settings, 'SITE_NAME', 'ARC Manager'),
            }
            
            # Template de bienvenida
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">🎉 ¡Bienvenido a {context['site_name']}!</h2>
                <p>Hola <strong>{username}</strong>,</p>
                <p>Tu cuenta ha sido creada exitosamente. ¡Ya puedes comenzar a usar el sistema!</p>
                <p><a href="{context['login_url']}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🚀 Acceder al Sistema</a></p>
                <p>Si tienes alguna pregunta, contacta a tu administrador.</p>
                <hr>
                <p><small>Este mensaje fue generado automáticamente.</small></p>
            </div>
            """
            
            text_content = f"""
            🎉 ¡Bienvenido a {context['site_name']}!
            
            Hola {username},
            
            Tu cuenta ha sido creada exitosamente. ¡Ya puedes comenzar a usar el sistema!
            
            🚀 Accede aquí: {context['login_url']}
            
            Si tienes alguna pregunta, contacta a tu administrador.
            
            {context['site_name']} - Sistema de Gestión
            """
            
            email = EmailMultiAlternatives(
                subject=subject or f'¡Bienvenido a {context["site_name"]}!',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            result = email.send()
            if result:
                logger.info(f"✅ [EMAIL] Email de bienvenida enviado a {user_email}")
            else:
                logger.error(f"❌ [EMAIL] Error enviando bienvenida a {user_email}")
        
        except Exception as e:
            logger.error(f"❌ [EMAIL] Excepción en bienvenida para {user_email}: {e}")
    
    thread = threading.Thread(target=_send_welcome, daemon=True)
    thread.start()
    
    return True

def test_email_configuration():
    """
    🧪 Función para testing de configuración
    """
    logger.info("🧪 [EMAIL] Iniciando test de configuración...")
    
    # Verificar configuración
    required_settings = [
        'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 
        'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)
    
    if missing_settings:
        logger.error(f"❌ [EMAIL] Configuraciones faltantes: {missing_settings}")
        return False
    
    logger.info("✅ [EMAIL] Configuración básica correcta")
    logger.info(f"   📧 HOST: {settings.EMAIL_HOST}")
    logger.info(f"   🔌 PORT: {settings.EMAIL_PORT}")
    logger.info(f"   📮 FROM: {settings.DEFAULT_FROM_EMAIL}")
    
    return True

# ========================================
# 🔄 FUNCIONES DE COMPATIBILIDAD
# ========================================

def send_new_user_email(user, password, request=None, background=True):
    """
    🔄 Función de compatibilidad con tu código existente
    Ahora usa el sistema de threading optimizado y tus templates existentes
    """
    user_email = user.email if hasattr(user, 'email') else str(user)
    username = user.username if hasattr(user, 'username') else user.first_name or user_email
    
    if background:
        return send_user_credentials_email(user_email, password, username, user_obj=user)
    else:
        # Para testing sincronizado
        logger.info(f"🔄 [EMAIL] Envío sincronizado solicitado para {user_email}")
        return send_user_credentials_email(user_email, password, username, user_obj=user)

def send_welcome_reminder_email(user, request=None):
    """
    🔄 Función de compatibilidad para bienvenida
    """
    user_email = user.email if hasattr(user, 'email') else str(user)
    username = user.username if hasattr(user, 'username') else user.first_name or user_email
    
    return send_welcome_email(user_email, username)