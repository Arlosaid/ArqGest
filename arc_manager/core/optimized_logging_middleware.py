"""
Middleware de logging optimizado para mínimo impacto en performance
"""
import logging
import time
import uuid
import random
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from core.logging_filters import set_request_id, clear_request_id, set_user_context, clear_user_context

logger = logging.getLogger('core.optimized_logging')


class OptimizedRequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware optimizado con sampling para mínimo impacto en performance.
    Solo loggea requests lentas, errores, y una muestra de requests normales.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configuración desde settings
        self.sample_rate = getattr(settings, 'LOG_SAMPLE_RATE', 0.01)  # 1% por defecto
        self.slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1000)  # 1 segundo
        self.log_requests = getattr(settings, 'LOG_REQUESTS', True)
    
    def __call__(self, request):
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
            
            # Solo loggear si es necesario
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
    
    def _get_or_create_request_id(self, request):
        """Obtiene request ID existente o crea uno nuevo"""
        # Reutilizar si viene del load balancer
        existing_id = request.META.get('HTTP_X_REQUEST_ID')
        if existing_id:
            return existing_id
        
        # Crear uno corto para performance
        return str(uuid.uuid4())[:8]
    
    def _log_request_if_needed(self, request, response, duration_ms):
        """Decide si debe loggear esta request basado en sampling y condiciones"""
        if not self.log_requests:
            return
        
        # Siempre loggear errores
        if response.status_code >= 400:
            self._log_request(request, response, duration_ms, 'error')
            return
        
        # Siempre loggear requests lentas
        if duration_ms > self.slow_threshold:
            self._log_request(request, response, duration_ms, 'slow')
            return
        
        # Sampling para requests normales
        if random.random() < self.sample_rate:
            self._log_request(request, response, duration_ms, 'sampled')
    
    def _log_request(self, request, response, duration_ms, reason):
        """Loggea una request con contexto completo"""
        user_id = None
        org_id = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            # Intentar obtener org_id si existe
            if hasattr(request.user, 'organization_id'):
                org_id = request.user.organization_id
        
        logger.info(
            f'Request {reason}',
            extra={
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration_ms, 2),
                'user_id': user_id,
                'organization_id': org_id,
                'client_ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
                'reason': reason,
            }
        )
    
    def _log_error(self, request, exception, duration_ms):
        """Loggea errores con contexto completo"""
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        logger.error(
            f'Request error: {type(exception).__name__}',
            extra={
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'duration_ms': round(duration_ms, 2),
                'user_id': user_id,
                'client_ip': self._get_client_ip(request),
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
            },
            exc_info=True
        )
    
    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
