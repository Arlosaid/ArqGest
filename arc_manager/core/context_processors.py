from django.conf import settings


def global_settings(request):
    """Inyecta configuraciones globales simples en templates."""
    return {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1.0'),
        'debug': getattr(settings, 'DEBUG', False),
    }


