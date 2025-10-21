# apps/main/middleware.py
from django.shortcuts import render
from django.conf import settings
from apps.main.models import SystemSettings


class MaintenanceModeMiddleware:
    """
    Middleware para modo mantenimiento.
    Cuando está activo, solo los superusuarios pueden acceder al sitio.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar configuración de modo mantenimiento
        sys_settings = SystemSettings.load()
        
        # Si el modo mantenimiento está activado
        if sys_settings.maintenance_mode:
            # Permitir acceso a superusuarios y staff
            if not (request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)):
                # Permitir acceso a URLs de admin para que puedan iniciar sesión
                if not request.path.startswith('/admin/'):
                    return render(request, 'maintenance.html', {
                        'maintenance_message': sys_settings.maintenance_message,
                        'support_email': sys_settings.support_email,
                        'company_name': sys_settings.company_name,
                    }, status=503)
        
        response = self.get_response(request)
        return response

