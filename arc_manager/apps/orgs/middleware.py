# arc_manager/apps/orgs/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings

class OrganizationContextMiddleware(MiddlewareMixin):
    """
    Este middleware inyecta el contexto de la organización en cada petición.
    Asume que el objeto request.user ya viene con la organización precargada
    si es necesario (optimizado en otro middleware).
    """
    def process_request(self, request):
        # Bypass middleware en modo testing
        if getattr(settings, 'TESTING', False):
            return None
            
        request.organization = None
        request.subscription = None
        
        if request.user.is_authenticated and not request.user.is_superuser:
            organization = getattr(request.user, 'organization', None)
            if organization:
                request.organization = organization
                
                # Cache de suscripción por 15 minutos para evitar consultas repetidas
                subscription_cache_key = f"org_subscription:{organization.id}"
                subscription = cache.get(subscription_cache_key)
                
                if subscription is None:
                    subscription = organization.get_subscription()
                    cache.set(subscription_cache_key, subscription, 900)  # 15 minutos
                
                request.subscription = subscription
        
        return None
