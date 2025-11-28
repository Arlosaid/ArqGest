from django.apps import AppConfig


class PlansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.plans'
    label = 'plans'
    
    def ready(self):
        # Importar signals para registrarlos
        import apps.plans.cache_signals  # noqa: F401
