from django.apps import AppConfig


class OrgsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orgs'
    label = 'orgs'
    
    def ready(self):
        # Importar signals para registrarlos
        import apps.orgs.cache_signals  # noqa: F401
