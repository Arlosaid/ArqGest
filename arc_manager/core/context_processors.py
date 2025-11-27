from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def global_settings(request):
    """Inyecta configuraciones globales simples en templates."""
    # Los límites de archivo están hardcodeados en el JS (1500MB)
    # Ya no se cargan desde SystemSettings para evitar problemas de caché
    
    return {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1.0'),
        'debug': getattr(settings, 'DEBUG', False),
        # Inject unified upload settings
        'MAX_UPLOAD_SIZE_MB': getattr(settings, 'MAX_UPLOAD_SIZE_MB', 1500),
        'ALLOWED_UPLOAD_EXTENSIONS': getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', []),
    }


