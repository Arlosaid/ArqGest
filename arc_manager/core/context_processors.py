from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def global_settings(request):
    """Inyecta configuraciones globales simples en templates."""
    from apps.main.models import SystemSettings
    
    try:
        system_settings = SystemSettings.load()
        max_file_size_mb = system_settings.max_file_size_mb
        max_file_size_mobile_mb = system_settings.upload_max_file_size_mobile_mb
        logger.debug(f"✅ Límites de archivo cargados: Desktop={max_file_size_mb}MB, Mobile={max_file_size_mobile_mb}MB")
    except Exception as e:
        max_file_size_mb = 500  # Fallback
        max_file_size_mobile_mb = 200  # Fallback
        logger.error(f"❌ Error cargando límites desde SystemSettings: {e}. Usando fallbacks")
    
    return {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1.0'),
        'debug': getattr(settings, 'DEBUG', False),
        'max_file_size_mb': max_file_size_mb,
        'max_file_size_mobile_mb': max_file_size_mobile_mb,
    }


