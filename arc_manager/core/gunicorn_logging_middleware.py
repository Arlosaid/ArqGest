"""
Middleware para agregar request_id a los logs de Gunicorn
"""
import logging
import uuid
from django.utils.deprecation import MiddlewareMixin

class GunicornRequestIdMiddleware(MiddlewareMixin):
    """
    Middleware que agrega request_id a los logs de Gunicorn
    """
    
    def process_request(self, request):
        """Agrega request_id al contexto de logging de Gunicorn"""
        # Generar request_id si no existe
        if not hasattr(request, 'request_id'):
            request.request_id = str(uuid.uuid4())[:8]
        
        # Agregar al contexto de logging
        logging.getLogger('gunicorn.access').info(
            f"Request started: {request.method} {request.path}",
            extra={'request_id': request.request_id}
        )
        
        return None
    
    def process_response(self, request, response):
        """Agrega request_id a la respuesta"""
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        
        return response
