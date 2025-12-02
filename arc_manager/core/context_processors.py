from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def global_settings(request):
    """Inyecta configuraciones globales simples en templates."""
    # Los límites de archivo están hardcodeados en el JS (1500MB)
    # Ya no se cargan desde SystemSettings para evitar problemas de caché
    
    context = {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1.0'),
        'debug': getattr(settings, 'DEBUG', False),
        # Inject unified upload settings
        'MAX_UPLOAD_SIZE_MB': getattr(settings, 'MAX_UPLOAD_SIZE_MB', 1500),
        'ALLOWED_UPLOAD_EXTENSIONS': getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', []),
        # Support info
        'SUPPORT_EMAIL': getattr(settings, 'SUPPORT_EMAIL', 'soporte@tuempresa.com'),
        'SUPPORT_PHONE': getattr(settings, 'SUPPORT_PHONE', '55 1234 5678'),
    }
    
    # Agregar información de storage si el usuario está autenticado y tiene organización
    if request.user.is_authenticated and hasattr(request.user, 'organization') and request.user.organization:
        try:
            from apps.orgs.storage_service import StorageService
            storage_summary = StorageService.get_storage_summary(request.user.organization)
            
            # Convertir remaining_gb a bytes para validación en frontend
            remaining_bytes = int(storage_summary['remaining_gb'] * 1024 * 1024 * 1024)
            
            context['STORAGE_INFO'] = {
                'available_bytes': remaining_bytes,
                'used_gb': storage_summary['used_gb'],
                'limit_gb': storage_summary['total_gb'],
                'remaining_gb': storage_summary['remaining_gb'],
                'usage_percentage': storage_summary['percentage'],
                'status': storage_summary['status'],
                'is_over_limit': storage_summary['is_over_limit'],
            }
        except Exception as e:
            logger.warning(f"Error loading storage info: {e}")
            context['STORAGE_INFO'] = None
    else:
        context['STORAGE_INFO'] = None
    
    return context


