# arc_manager/apps/orgs/middleware.py
from django.utils.deprecation import MiddlewareMixin

class OrganizationContextMiddleware(MiddlewareMixin):
    """
    Este middleware inyecta el contexto de la organización en cada petición.
    Asume que el objeto request.user ya viene con la organización precargada
    si es necesario (optimizado en otro middleware).
    """
    def process_request(self, request):
        request.organization = None
        request.subscription = None
        
        if request.user.is_authenticated and not request.user.is_superuser:
            organization = getattr(request.user, 'organization', None)
            if organization:
                request.organization = organization
                # La función get_subscription() debería estar cacheada en el modelo Organization
                request.subscription = organization.get_subscription()
        
        return None
