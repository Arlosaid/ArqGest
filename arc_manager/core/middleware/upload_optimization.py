# core/middleware/upload_optimization.py
"""
Middleware de optimización para uploads grandes
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class UploadOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware que optimiza uploads grandes automáticamente
    """
    
    def process_request(self, request):
        """Optimizar request para uploads grandes"""
        
        # Detectar uploads grandes
        content_length = request.META.get('CONTENT_LENGTH', 0)
        if content_length:
            try:
                content_length = int(content_length)
                
                # Si es upload grande (>100MB), aplicar optimizaciones
                if content_length > 100 * 1024 * 1024:
                    self._optimize_large_upload(request, content_length)
                    
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _optimize_large_upload(self, request, content_length):
        """Aplicar optimizaciones específicas para uploads grandes"""
        
        # Marcar como upload grande para tracking
        request.is_large_upload = True
        request.upload_size_mb = content_length / (1024 * 1024)
        request.upload_start_time = time.time()
        
        # Log inicio de upload grande
        logger.info(
            f"🚀 Large upload detected: {request.upload_size_mb:.1f}MB "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        
        # Optimizaciones de memoria para uploads grandes
        if hasattr(settings, 'FILE_UPLOAD_HANDLERS'):
            # Forzar uso de archivo temporal para uploads grandes
            request.upload_handlers = [
                handler for handler in settings.FILE_UPLOAD_HANDLERS 
                if 'Memory' not in handler or content_length <= settings.DATA_UPLOAD_MAX_MEMORY_SIZE
            ]
        
        # Headers de optimización
        request.META['HTTP_X_LARGE_UPLOAD'] = 'true'
        request.META['HTTP_X_UPLOAD_SIZE'] = str(content_length)
    
    def process_response(self, request, response):
        """Log resultado de uploads grandes"""
        
        if hasattr(request, 'is_large_upload') and request.is_large_upload:
            duration = time.time() - request.upload_start_time
            
            # Log resultado
            if response.status_code < 400:
                logger.info(
                    f"✅ Large upload completed: {request.upload_size_mb:.1f}MB "
                    f"in {duration:.1f}s ({request.upload_size_mb/duration:.1f}MB/s)"
                )
            else:
                logger.warning(
                    f"❌ Large upload failed: {request.upload_size_mb:.1f}MB "
                    f"after {duration:.1f}s - Status: {response.status_code}"
                )
        
        return response


class R2ConnectionPoolMiddleware(MiddlewareMixin):
    """
    Middleware para optimizar pool de conexiones R2
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.r2_client = None
        self._initialize_r2_client()
    
    def _initialize_r2_client(self):
        """Inicializar cliente R2 compartido"""
        try:
            from core.r2_config import get_optimized_r2_client
            self.r2_client = get_optimized_r2_client()
            logger.info("✅ R2 connection pool initialized")
        except Exception as e:
            logger.warning(f"⚠️ R2 connection pool not available: {e}")
    
    def process_request(self, request):
        """Proporcionar cliente R2 optimizado al request"""
        if self.r2_client:
            request.r2_client = self.r2_client
        return None


class UploadProgressMiddleware(MiddlewareMixin):
    """
    Middleware para tracking de progreso de uploads
    """
    
    def process_request(self, request):
        """Inicializar tracking de progreso"""
        
        if request.method == 'POST' and 'multipart/form-data' in request.content_type:
            # Generar ID único para tracking
            import uuid
            request.upload_id = str(uuid.uuid4())
            
            # Almacenar en caché para tracking
            from django.core.cache import cache
            cache.set(f"upload_progress_{request.upload_id}", {
                'status': 'starting',
                'progress': 0,
                'size': request.META.get('CONTENT_LENGTH', 0),
                'start_time': time.time()
            }, timeout=3600)  # 1 hora
        
        return None
    
    def process_response(self, request, response):
        """Finalizar tracking de progreso"""
        
        if hasattr(request, 'upload_id'):
            from django.core.cache import cache
            
            # Actualizar progreso final
            final_status = 'completed' if response.status_code < 400 else 'failed'
            cache.set(f"upload_progress_{request.upload_id}", {
                'status': final_status,
                'progress': 100 if final_status == 'completed' else 0,
                'end_time': time.time()
            }, timeout=300)  # 5 minutos para cleanup
        
        return response
