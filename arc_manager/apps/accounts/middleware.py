# middleware.py
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.http import HttpResponseServerError, JsonResponse
from django.template import loader
import logging
import re
from django.utils import timezone

logger = logging.getLogger('apps.accounts')
User = get_user_model()

class LoginRequiredMiddleware:
    """
    Middleware que requiere autenticación y precarga datos del usuario.
    - Redirige si el usuario no está autenticado y la URL no es pública.
    - Si el usuario está autenticado, precarga su organización para optimizar
      el acceso en middlewares y vistas posteriores.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [re.compile(url) for url in getattr(settings, 'LOGIN_EXEMPT_URLS', [])]
        self.login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        client_ip = self.get_client_ip(request)
        
        if not request.user.is_authenticated:
            # Si no está autenticado, verificar si la URL es pública
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                logger.debug(f"Acceso no autenticado bloqueado - IP: {client_ip}, Path: /{path}")
                return redirect(f'{self.login_url}?next=/{path}')
        else:
            # Si está autenticado, optimizar el objeto user
            # Usamos una property para evitar una consulta si no se accede a la organización
            # Pero para asegurar que esté disponible en todo el request, la cargamos aquí.
            try:
                request.user = User.objects.select_related('organization').get(pk=request.user.pk)
                logger.debug(f"Usuario autenticado cargado - {request.user.email}, Path: /{path}")
            except User.DoesNotExist:
                # Caso muy raro: el usuario fue borrado durante su sesión.
                logger.error(f"Usuario autenticado no encontrado en BD - ID: {request.user.pk}, IP: {client_ip}")
                # Dejamos que el flujo normal de Django lo desautentique.
                pass

        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip


class PasswordChangeRequiredMiddleware:
    """
    Middleware que intercepta usuarios que necesiten cambiar su contraseña.
    Redirige a la página de cambio forzado de contraseña.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que están exentas de la verificación de cambio de contraseña
        self.exempt_urls = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/force-password-change/',
            '/admin/',  # Para que los admins puedan cambiar contraseñas desde el panel
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Solo verificar si el usuario está autenticado
        if request.user.is_authenticated and hasattr(request.user, 'password_change_required'):
            # Si necesita cambiar contraseña y no está en una URL exenta
            if (request.user.password_change_required and 
                not any(request.path.startswith(url) for url in self.exempt_urls)):
                
                client_ip = self.get_client_ip(request)
                logger.info(
                    f"Redirigiendo a cambio de contraseña - Usuario: {request.user.email}, "
                    f"IP: {client_ip}, Path solicitado: {request.path}"
                )
                
                # Redirigir a la página de cambio forzado de contraseña
                return redirect('/accounts/force-password-change/')

        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip


class SuperuserRestrictMiddleware:
    """
    Middleware para restringir acceso al admin panel solo a superusers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            re.compile(r'^admin/.*$'),
            re.compile(r'^accounts/logout/?$'),
            re.compile(r'^accounts/login/?$'),
            re.compile(r'^static/.*$'),
            re.compile(r'^media/.*$'),
        ]

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            path = request.path.lstrip('/')
            client_ip = self.get_client_ip(request)
            
            # Permitir acceso al panel de admin
            if path.startswith('admin/'):
                if 'admin_welcome_shown' not in request.session and request.path == '/admin/' and request.method == 'GET':
                    logger.info(f"Superusuario accedió al admin - {request.user.email}, IP: {client_ip}")
                    messages.info(request, "Bienvenido al panel administrativo. Desde aquí puedes gestionar todo el sistema.")
                    request.session['admin_welcome_shown'] = True
                return self.get_response(request)

            # Bloquear acceso al resto de la app
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                logger.warning(
                    f"Superusuario intentó acceder a app principal - {request.user.email}, "
                    f"IP: {client_ip}, Path: /{path} - Redirigido a admin"
                )
                return redirect('/admin/')
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip

    
class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware para manejo de errores en producción.
    Asegura que nunca se muestren errores genéricos de Railway.
    """
    
    def process_exception(self, request, exception):
        if not settings.DEBUG:
            client_ip = self.get_client_ip(request)
            user_info = 'Anónimo'
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"{request.user.email} (ID: {request.user.pk})"
            
            logger.error(
                f"Error no manejado - Usuario: {user_info}, IP: {client_ip}, "
                f"Path: {request.path}, Método: {request.method}, Error: {str(exception)}",
                exc_info=True,
                extra={
                    'request': request,
                    'user': request.user if hasattr(request, 'user') else None,
                    'path': request.path,
                    'method': request.method,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'client_ip': client_ip,
                }
            )
            
            # Para requests AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                logger.info(f"Error 500 devuelto como JSON para request AJAX - IP: {client_ip}")
                return JsonResponse({
                    'error': 'Error interno del servidor',
                    'status': 500
                }, status=500)
            
            # Para requests normales, usar template personalizado
            try:
                template = loader.get_template('500.html')
                logger.info(f"Error 500 mostrado con template personalizado - IP: {client_ip}")
                return HttpResponseServerError(template.render({}))
            except Exception as e:
                # Fallback si no se puede cargar el template
                logger.error(f"No se pudo cargar template 500.html: {str(e)} - IP: {client_ip}")
                return HttpResponseServerError(
                    """
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <title>Error del Servidor - ARC Manager</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
                            .error { max-width: 400px; margin: 0 auto; }
                            h1 { color: #dc3545; font-size: 3rem; }
                            p { color: #6c757d; margin: 1rem 0; }
                            .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; 
                                   text-decoration: none; border-radius: 5px; }
                        </style>
                    </head>
                    <body>
                        <div class="error">
                            <h1>500</h1>
                            <h2>Error del servidor</h2>
                            <p>Algo salió mal. Por favor, inténtalo de nuevo más tarde.</p>
                            <a href="/" class="btn">Ir al inicio</a>
                        </div>
                    </body>
                    </html>
                    """
                )
        
        return None
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip
