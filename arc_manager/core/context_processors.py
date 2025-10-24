from django.conf import settings


def global_settings(request):
    """Inyecta configuraciones globales simples en templates."""
    from apps.main.models import SystemSettings
    
    try:
        system_settings = SystemSettings.load()
        max_file_size_mb = system_settings.max_file_size_mb
    except:
        max_file_size_mb = 500  # Fallback
    
    return {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1.0'),
        'debug': getattr(settings, 'DEBUG', False),
        'max_file_size_mb': max_file_size_mb,
    }


