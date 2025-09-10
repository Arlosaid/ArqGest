"""
Middleware especializado para logging de errores 500 y monitoreo del sistema.
"""
import logging
import time
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from core.error_codes import log_operation, SystemErrorCodes

logger = logging.getLogger('core.error_handler')


class Enhanced500LoggingMiddleware(MiddlewareMixin):
    """
    Middleware que captura TODOS los errores 500 y los registra con información detallada.
    Se ejecuta ANTES del ErrorHandlingMiddleware para capturar errores específicos.
    """
    
    def process_exception(self, request, exception):
        """
        Procesa todas las excepciones no manejadas y las registra con detalle completo.
        """
        # Obtener información del usuario
        user_email = 'anonymous'
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_email = request.user.email
            user_id = request.user.id
        
        # Obtener IP del cliente
        client_ip = self.get_client_ip(request)
        
        # Determinar el código de error según el tipo de excepción
        error_code = self._get_error_code_from_exception(exception)
        
        # Información detallada de la request
        request_data = {
            'path': request.path,
            'method': request.method,
            'user_id': user_id,
            'client_ip': client_ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'is_ajax': self._is_ajax_request(request),
            'is_htmx': request.headers.get('HX-Request') == 'true',
            'content_type': request.content_type,
            'query_params': dict(request.GET),
        }
        
        # Solo incluir POST data si no es sensible
        if request.method == 'POST' and not self._contains_sensitive_data(request.path):
            try:
                request_data['post_data'] = dict(request.POST)
            except:
                request_data['post_data'] = 'Could not parse POST data'
        
        # Información de la excepción
        exception_data = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'exception_module': getattr(exception.__class__, '__module__', 'unknown'),
            'traceback': traceback.format_exc(),
        }
        
        # Log estructurado completo
        log_operation(
            'HTTP_500_ERROR',
            user_email,
            logger,
            level='ERROR',
            error_code=error_code,
            **request_data,
            **exception_data
        )
        
        # En desarrollo, también imprimir a consola para debugging
        if settings.DEBUG:
            print(f"\n🚨 ERROR 500 CAPTURED:")
            print(f"   Path: {request.path}")
            print(f"   User: {user_email}")
            print(f"   Error: {type(exception).__name__}: {str(exception)}")
            print(f"   Code: {error_code}")
            print(f"   IP: {client_ip}")
            print(f"   Traceback: {traceback.format_exc()}")
            print("="*80)
        
        # No retornar nada para que otros middlewares puedan manejar la respuesta
        return None
    
    def _get_error_code_from_exception(self, exception):
        """Determina el código de error basado en el tipo de excepción."""
        exception_name = type(exception).__name__
        
        if 'DoesNotExist' in exception_name:
            return SystemErrorCodes.SYSTEM_DB_INTEGRITY_ERROR
        elif 'PermissionDenied' in exception_name:
            return SystemErrorCodes.SYSTEM_MIDDLEWARE_PERMISSION_ERROR
        elif 'ValidationError' in exception_name:
            return SystemErrorCodes.SYSTEM_MIDDLEWARE_AUTH_ERROR
        elif 'IntegrityError' in exception_name:
            return SystemErrorCodes.SYSTEM_DB_INTEGRITY_ERROR
        elif 'DatabaseError' in exception_name or 'OperationalError' in exception_name:
            return SystemErrorCodes.SYSTEM_DB_CONNECTION_ERROR
        elif 'TimeoutError' in exception_name:
            return SystemErrorCodes.SYSTEM_DB_TIMEOUT
        else:
            return SystemErrorCodes.SYSTEM_MIDDLEWARE_UNEXPECTED_ERROR
    
    def _is_ajax_request(self, request):
        """Determina si es una request AJAX."""
        return (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.headers.get('HX-Request') == 'true' or
            'application/json' in request.headers.get('Accept', '')
        )
    
    def _contains_sensitive_data(self, path):
        """Determina si la URL podría contener datos sensibles."""
        sensitive_paths = [
            '/accounts/login',
            '/accounts/password',
            '/admin/',
            '/api/auth/',
        ]
        return any(sensitive_path in path for sensitive_path in sensitive_paths)
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de rendimiento de requests.
    """
    
    def process_request(self, request):
        """Marca el tiempo de inicio de la request."""
        request._start_time = time.time()
    
    def process_response(self, request, response):
        """Log del tiempo de respuesta si es lento."""
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000  # ms
            
            # Log requests lentas (>2 segundos)
            if duration > 2000:
                user_email = 'anonymous'
                if hasattr(request, 'user') and request.user.is_authenticated:
                    user_email = request.user.email
                
                log_operation(
                    'SLOW_REQUEST',
                    user_email,
                    logger,
                    level='WARNING',
                    error_code='PERF_SLOW_REQUEST',
                    path=request.path,
                    method=request.method,
                    duration_ms=round(duration, 2),
                    status_code=response.status_code,
                    client_ip=self.get_client_ip(request)
                )
        
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DatabaseErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware específico para capturar errores de base de datos.
    """
    
    def process_exception(self, request, exception):
        """Captura específicamente errores de base de datos."""
        from django.db import DatabaseError, IntegrityError
        
        if isinstance(exception, (DatabaseError, IntegrityError)):
            user_email = 'anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_email = request.user.email
            
            error_code = SystemErrorCodes.SYSTEM_DB_INTEGRITY_ERROR
            if 'timeout' in str(exception).lower():
                error_code = SystemErrorCodes.SYSTEM_DB_TIMEOUT
            elif 'connection' in str(exception).lower():
                error_code = SystemErrorCodes.SYSTEM_DB_CONNECTION_ERROR
            
            log_operation(
                'DATABASE_ERROR',
                user_email,
                logger,
                level='ERROR',
                error_code=error_code,
                path=request.path,
                method=request.method,
                exception_type=type(exception).__name__,
                exception_message=str(exception),
                client_ip=self.get_client_ip(request)
            )
        
        return None
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
