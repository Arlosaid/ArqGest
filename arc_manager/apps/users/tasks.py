from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def send_user_credentials_email(self, user_id, password, request_data=None):
    """
    Tarea asíncrona para enviar credenciales de usuario por email.
    
    Args:
        user_id: ID del usuario
        password: Contraseña temporal
        request_data: Datos de la request (opcional)
    
    Returns:
        bool: True si el email se envió correctamente
    """
    try:
        # Obtener el usuario
        user = User.objects.get(id=user_id)
        
        logger.info(f"🚀 [ASYNC] Iniciando envío de credenciales para {user.email}")
        
        # Verificar configuración de email
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'No configurado')
        email_host = getattr(settings, 'EMAIL_HOST', 'No configurado')
        default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')
        
        logger.info(f"📧 [ASYNC] Configuración EMAIL_BACKEND: {email_backend}")
        logger.info(f"📧 [ASYNC] Configuración EMAIL_HOST: {email_host}")
        logger.info(f"📧 [ASYNC] Configuración DEFAULT_FROM_EMAIL: {default_from_email}")
        
        # Obtener el site_name
        site_name = getattr(settings, 'SITE_NAME', 'ARC Manager')
        
        # Construir la URL de login
        if request_data and 'HTTP_HOST' in request_data:
            protocol = 'https' if request_data.get('is_secure', False) else 'http'
            login_url = f"{protocol}://{request_data['HTTP_HOST']}/accounts/login/"
        else:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            login_url = f"{base_url}/accounts/login/"
        
        logger.info(f"🔗 [ASYNC] URL de login generada: {login_url}")
        
        # Preparar el contexto para el template
        context = {
            'user': user,
            'password': password,
            'site_name': site_name,
            'login_url': login_url
        }
        
        logger.info(f"📝 [ASYNC] Renderizando template HTML...")
        # Renderizar los templates HTML y texto plano
        html_message = render_to_string('users/emails/new_user_credentials.html', context)
        logger.info(f"✅ [ASYNC] Template HTML renderizado correctamente")
        
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
        
        logger.info(f"📬 [ASYNC] Preparando email: {subject}")
        logger.info(f"📤 [ASYNC] De: {from_email} -> Para: {user.email}")
        
        # Usar EmailMultiAlternatives para enviar tanto HTML como texto plano
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=to_emails
        )
        email.attach_alternative(html_message, "text/html")
        
        logger.info(f"🔌 [ASYNC] Estableciendo conexión SMTP...")
        logger.info(f"📨 [ASYNC] Enviando email...")
        
        # Enviar con timeout optimizado y conexión persistente
        import socket
        import time
        from django.core.mail import get_connection
        
        start_time = time.time()
        try:
            # Usar conexión SMTP con timeout optimizado
            connection = get_connection(
                backend=settings.EMAIL_BACKEND,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                use_ssl=settings.EMAIL_USE_SSL,
                timeout=getattr(settings, 'EMAIL_TIMEOUT', 60),
                fail_silently=False
            )
            
            # Configurar timeout de socket más agresivo
            default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(60)  # 60 segundos timeout
            
            # Enviar usando la conexión optimizada
            email.connection = connection
            email.send()
            
            # Cerrar conexión
            connection.close()
            
            # Restaurar timeout original
            socket.setdefaulttimeout(default_timeout)
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ [ASYNC] Email enviado exitosamente en {elapsed_time:.2f}s a {user.email}")
            return True
            
        except socket.timeout:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ [ASYNC] Timeout enviando email a {user.email} ({elapsed_time:.0f}s)")
            # Reintentar la tarea
            raise self.retry(countdown=60, exc=socket.timeout)
        except Exception as smtp_error:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ [ASYNC] Error SMTP enviando email a {user.email} ({elapsed_time:.0f}s): {str(smtp_error)}")
            # Reintentar la tarea
            raise self.retry(countdown=60, exc=smtp_error)
        finally:
            # Asegurar que se restaure el timeout
            socket.setdefaulttimeout(default_timeout)
        
    except User.DoesNotExist:
        logger.error(f"❌ [ASYNC] Usuario con ID {user_id} no encontrado")
        return False
    except Exception as e:
        logger.error(f"❌ [ASYNC] Error general enviando email a usuario {user_id}: {str(e)}")
        logger.error(f"❌ [ASYNC] Tipo de error: {type(e).__name__}")
        
        # Reintentar la tarea si no es el último intento
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 [ASYNC] Reintentando envío de email (intento {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=60, exc=e)
        
        return False

@shared_task(bind=True, max_retries=3)
def send_bulk_user_credentials(self, user_data_list, request_data=None):
    """
    Tarea asíncrona para enviar credenciales a múltiples usuarios.
    
    Args:
        user_data_list: Lista de diccionarios con user_id y password
        request_data: Datos de la request (opcional)
    
    Returns:
        dict: Resumen de envíos exitosos y fallidos
    """
    success_count = 0
    error_count = 0
    total_users = len(user_data_list)
    
    logger.info(f"🚀 [ASYNC] Iniciando envío masivo de credenciales a {total_users} usuarios")
    
    for i, user_data in enumerate(user_data_list, 1):
        try:
            user_id = user_data['user_id']
            password = user_data['password']
            
            logger.info(f"📧 [ASYNC] Procesando usuario {i}/{total_users}: ID {user_id}")
            
            # Enviar email individual
            result = send_user_credentials_email.delay(user_id, password, request_data)
            
            if result.get():
                success_count += 1
                logger.info(f"✅ [ASYNC] Email programado para usuario {user_id}")
            else:
                error_count += 1
                logger.error(f"❌ [ASYNC] Error programando email para usuario {user_id}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ [ASYNC] Excepción procesando usuario {i}: {str(e)}")
    
    logger.info(f"📊 [ASYNC] Resumen: {success_count} programados, {error_count} fallidos")
    
    return {
        'success_count': success_count,
        'error_count': error_count,
        'total_users': total_users
    }
