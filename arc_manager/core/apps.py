"""
Configuración de la aplicación Core de Django.

Este módulo define CoreConfig, que gestiona la inicialización de la app core.
El método ready() se ejecuta después de que Django ha cargado todas las apps,
permitiendo importar signals de forma segura.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuración de la aplicación Core.
    
    Gestiona la inicialización de signals de seguridad (Axes) y otros
    componentes que requieren que Django esté completamente cargado.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """
        Método ejecutado cuando Django ha cargado todas las apps.
        
        Importa signals aquí para evitar errores de AppRegistryNotReady.
        Los signals deben importarse después de que los modelos estén disponibles.
        """
        # Importar signals de Axes (user_locked_out, user_login_failed)
        try:
            from . import signals  # noqa: F401
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No se pudieron cargar signals de core: {e}")
