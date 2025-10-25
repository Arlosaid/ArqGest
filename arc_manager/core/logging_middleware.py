"""
Middleware de logging para mínimo impacto en performance
"""
import logging
import time
import uuid
import random
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from core.logging_filters import set_request_id, clear_request_id, set_user_context, clear_user_context

logger = logging.getLogger('core.logging')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware optimizado con sampling para mínimo impacto en performance.
    Solo loggea requests lentas, errores, y una muestra de requests normales.
    EXCLUYE automáticamente archivos estáticos para reducir ruido.
    """
    
    # Rutas estáticas que nunca deben loguearse (reducir ruido en 90%)
    STATIC_PATHS = (
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
        '/__debug__/',  # Django Debug Toolbar
    )
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configuración desde settings - optimizada para mínimo overhead
        self.log_requests = getattr(settings, 'LOG_REQUESTS', True)
        self.log_only_errors = getattr(settings, 'LOG_ONLY_ERRORS', False)
        self.log_slow_requests = getattr(settings, 'LOG_SLOW_REQUESTS', True)
        self.slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2000)  # 2 segundos
        self.sample_rate = getattr(settings, 'SAMPLE_RATE', 0)  # 0 = sin sampling por defecto
    
    def __call__(self, request):
        # OPTIMIZACIÓN: Excluir archivos estáticos inmediatamente (sin overhead)
        if self._is_static_request(request):
            return self.get_response(request)
        
        # Generar o reutilizar request ID
        request_id = self._get_or_create_request_id(request)
        request.request_id = request_id
        set_request_id(request_id)
        
        # Establecer contexto del usuario si está autenticado
        user_id = None
        organization_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            # Intentar obtener organization_id si existe
            if hasattr(request.user, 'organization_id'):
                organization_id = request.user.organization_id
        
        set_user_context(user_id, organization_id)
        
        start_time = time.perf_counter()
        
        try:
            response = self.get_response(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Solo loggear si es necesario (para requests lentas/errores)
            self._log_request_if_needed(request, response, duration_ms)
            
            # Agregar request ID a headers de respuesta
            response['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            # Siempre loggear errores
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_error(request, e, duration_ms)
            raise
        finally:
            clear_request_id()
            clear_user_context()
    
    def _is_static_request(self, request):
        """Detecta si es un request a archivos estáticos (reducir ruido en 90%)"""
        path = request.path
        return any(path.startswith(static_path) for static_path in self.STATIC_PATHS)
    
    def _get_or_create_request_id(self, request):
        """Obtiene request ID existente o crea uno nuevo"""
        # Reutilizar si viene del load balancer
        existing_id = request.META.get('HTTP_X_REQUEST_ID')
        if existing_id:
            return existing_id
        
        # Crear uno corto para performance
        return str(uuid.uuid4())[:8]
    
    def _log_request_if_needed(self, request, response, duration_ms):
        """Decide si debe loggear esta request basado en configuración optimizada"""
        if not self.log_requests:
            return
        
        status_code = response.status_code
        is_error = status_code >= 400
        is_slow = duration_ms > self.slow_threshold
        
        # Modo profesional: solo errores y requests muy lentas
        if is_error:
            self._log_request(request, response, duration_ms, 'error')
        elif self.log_slow_requests and is_slow:
            self._log_request(request, response, duration_ms, 'slow')
    
    def _log_request(self, request, response, duration_ms, reason):
        """Loggea una request con formato profesional y conciso"""
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        # Usar el logger de Django para consistencia
        django_logger = logging.getLogger('django.server')
        
        # Formato profesional y conciso
        if reason == 'error':
            # Solo para errores HTTP (4xx, 5xx)
            django_logger.warning(
                f'HTTP {response.status_code} | {request.method} {request.path} | User: {user_id or "Anonymous"} | {round(duration_ms, 0)}ms',
                extra={'request_id': request.request_id, 'user_id': user_id}
            )
        elif reason == 'slow':
            # Solo para requests muy lentas
            django_logger.warning(
                f'SLOW REQUEST | {request.method} {request.path} | User: {user_id or "Anonymous"} | {round(duration_ms, 0)}ms',
                extra={'request_id': request.request_id, 'user_id': user_id}
            )
    
    def _log_error(self, request, exception, duration_ms):
        """Loggea errores del middleware con formato profesional"""
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        django_logger = logging.getLogger('django.server')
        
        # Formato profesional y conciso para errores del middleware
        django_logger.error(
            f'MIDDLEWARE ERROR | {request.method} {request.path} | User: {user_id or "Anonymous"} | {round(duration_ms, 0)}ms | {type(exception).__name__}',
            extra={'request_id': request.request_id, 'user_id': user_id}
        )
    
    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
