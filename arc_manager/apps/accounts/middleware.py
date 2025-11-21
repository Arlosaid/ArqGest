
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
from core.error_codes import SystemErrorCodes
from core.structured_logging import log_error

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
        # Bypass middleware en modo testing
        if getattr(settings, 'TESTING', False):
            return self.get_response(request)
            
        path = request.path_info.lstrip('/')
        
        if not request.user.is_authenticated:
            # Si no está autenticado, verificar si la URL es pública
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                # NO loguear - esto se ejecuta en CADA request no autenticado
                # Generaría spam masivo
                return redirect(f'{self.login_url}?next=/{path}')
        else:
            # Si está autenticado, optimizar el objeto user
            try:
                request.user = User.objects.select_related('organization').get(pk=request.user.pk)
            except User.DoesNotExist:
                # Caso muy raro: el usuario fue borrado durante su sesión
                logger.error(
                    f"USUARIO AUTENTICADO NO ENCONTRADO | User ID: {request.user.pk}"
                )
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
        # Bypass middleware en modo testing
        if getattr(settings, 'TESTING', False):
            return self.get_response(request)
            
        # Solo verificar si el usuario está autenticado
        if request.user.is_authenticated and hasattr(request.user, 'password_change_required'):
            # Si necesita cambiar contraseña y no está en una URL exenta
            if (request.user.password_change_required and 
                not any(request.path.startswith(url) for url in self.exempt_urls)):
                
                # NO loguear - esto se ejecuta en CADA request
                # Solo loguear en la vista de password change
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
        # Bypass middleware en modo testing
        if getattr(settings, 'TESTING', False):
            return self.get_response(request)
            
        if request.user.is_authenticated and request.user.is_superuser:
            path = request.path.lstrip('/')
            
            # Permitir acceso al panel de admin
            if path.startswith('admin/'):
                if 'admin_welcome_shown' not in request.session and request.path == '/admin/' and request.method == 'GET':
                    messages.info(request, "Bienvenido al panel administrativo. Desde aquí puedes gestionar todo el sistema.")
                    request.session['admin_welcome_shown'] = True
                return self.get_response(request)

            # Bloquear acceso al resto de la app para superusers
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                # NO loguear - esto se ejecuta en CADA request de superuser
                # Solo loguear el login de superuser (ya está en views.py)
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
    
    Maneja errores 400, 403, 500 con notificaciones + redirect.
    Los 404 usan su template normal (son comunes y no críticos).
    """
    
    def process_exception(self, request, exception):
        """
        Maneja excepciones no capturadas (principalmente 500).
        NO loguea (ya lo hace Django automáticamente).
        Muestra notificación amigable usando messages.
        """
        if not settings.DEBUG:
            # Para requests AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Error interno del servidor',
                    'status': 500
                }, status=500)
            
            # Para requests normales: usar sistema de messages + redirect
            # NO mostrar template 500.html, usar notificaciones
            messages.error(
                request, 
                'Algo salió mal de nuestro lado. Ya estamos trabajando en solucionarlo. '
                'Por favor, intenta nuevamente en unos momentos.'
            )
            
            # Redirigir al dashboard o página principal
            return redirect('main:dashboard')
        
        # En desarrollo, dejar que Django maneje la excepción normalmente
        return None
    
    def process_response(self, request, response):
        """
        Intercepta respuestas de error para convertirlas en notificaciones.
        Solo para 400 y 403. Los 404 y 500 se manejan en otros lugares.
        """
        if not settings.DEBUG and hasattr(response, 'status_code'):
            # 400 Bad Request
            if response.status_code == 400:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'La solicitud no pudo procesarse. Por favor, intenta nuevamente.',
                        'status': 400
                    }, status=400)
                
                messages.warning(
                    request,
                    'La información enviada no es válida. Por favor, verifica e intenta nuevamente.'
                )
                referer = request.META.get('HTTP_REFERER')
                if referer and request.build_absolute_uri() != referer:
                    return redirect(referer)
                return redirect('main:dashboard')
            
            # 403 Forbidden
            elif response.status_code == 403:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'No tienes permiso para acceder a este recurso.',
                        'status': 403
                    }, status=403)
                
                messages.error(
                    request,
                    'No tienes permisos para acceder a esta página. Si crees que esto es un error, contacta con tu administrador.'
                )
                referer = request.META.get('HTTP_REFERER')
                if referer and request.build_absolute_uri() != referer:
                    return redirect(referer)
                return redirect('main:dashboard')
            
            # 404 Not Found - MANTENER TEMPLATE (no interceptar)
            # Los 404 son comunes y esperados, merecen su propia página
            # El handler404 en urls.py se encarga de esto
        
        return response
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip
