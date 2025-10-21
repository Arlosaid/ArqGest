from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.main'
    verbose_name = 'Principal'

    def ready(self):
        """Configuración cuando la app está lista."""
        # Importar signals para auto-sincronización
        import apps.main.signals
        # Importar el admin para aplicar personalizaciones
        from . import admin