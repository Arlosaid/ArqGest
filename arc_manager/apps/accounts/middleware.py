# middleware.py
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.http import HttpResponseServerError
from django.template import loader
import logging
import re

logger = logging.getLogger(__name__)
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
        
        if not request.user.is_authenticated:
            # Si no está autenticado, verificar si la URL es pública
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                return redirect(f'{self.login_url}?next=/{path}')
        else:
            # Si está autenticado, optimizar el objeto user
            # Usamos una property para evitar una consulta si no se accede a la organización
            # Pero para asegurar que esté disponible en todo el request, la cargamos aquí.
            try:
                request.user = User.objects.select_related('organization').get(pk=request.user.pk)
            except User.DoesNotExist:
                # Caso muy raro: el usuario fue borrado durante su sesión.
                # Dejamos que el flujo normal de Django lo desautentique.
                pass

        response = self.get_response(request)
        return response


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
            
            # Permitir acceso al panel de admin
            if path.startswith('admin/'):
                if 'admin_welcome_shown' not in request.session and request.path == '/admin/' and request.method == 'GET':
                    messages.info(request, "Bienvenido al panel administrativo. Desde aquí puedes gestionar todo el sistema.")
                    request.session['admin_welcome_shown'] = True
                return self.get_response(request)

            # Bloquear acceso al resto de la app
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                return redirect('/admin/')
        
        response = self.get_response(request)
        return response

    
class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware para manejo de errores en producción.
    """
    
    def process_exception(self, request, exception):
        if not settings.DEBUG:
            logger.error(
                f"Error no manejado en {request.path}: {str(exception)}",
                exc_info=True,
                extra={
                    'request': request,
                    'user': request.user if hasattr(request, 'user') else None,
                }
            )
            
            try:
                template = loader.get_template('500.html')
                return HttpResponseServerError(template.render({}))
            except Exception:
                return HttpResponseServerError("<h1>Error del Servidor</h1><p>Ha ocurrido un error interno.</p>")
        
        return None
