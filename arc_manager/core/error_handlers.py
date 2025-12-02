"""
Handlers personalizados para errores HTTP.
En lugar de mostrar páginas de error completas, usa el sistema de notificaciones
de la app para mostrar mensajes amigables al usuario.
Los detalles técnicos solo van a los logs del backend.

IMPORTANTE: Los logs ya se generan automáticamente en:
- logging_middleware.py (para requests HTTP)
- structured_logging.py (para errores de aplicación)

Este módulo solo debe:
1. Mostrar notificaciones amigables al usuario
2. Redirigir apropiadamente
3. NO duplicar logs que ya se generan en el middleware
"""
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse, NoReverseMatch

logger = logging.getLogger(__name__)


def _get_safe_redirect_url(request):
    """
    Obtener URL de redirección segura.
    Intenta redirigir al referer, luego al dashboard, y finalmente a la raíz.
    """
    # Intentar redirigir a la página anterior
    referer = request.META.get('HTTP_REFERER')
    if referer and request.build_absolute_uri() != referer:
        return referer
    
    # Intentar redirigir al dashboard
    try:
        return reverse('dashboard')
    except NoReverseMatch:
        pass
    
    # Intentar con namespace
    try:
        return reverse('main:dashboard')
    except NoReverseMatch:
        pass
    
    # Fallback a la raíz
    return '/'


def custom_400_view(request, exception=None):
    """
    Handler personalizado para errores 400 (Bad Request).
    NO loguea (ya lo hace el middleware automáticamente).
    """
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'La solicitud no pudo procesarse. Por favor, intenta nuevamente.',
            'status': 400
        }, status=400)
    
    # Para requests normales: mensaje amigable y redirigir
    messages.warning(request, 'La información enviada no es válida. Por favor, verifica e intenta nuevamente.')
    
    return HttpResponseRedirect(_get_safe_redirect_url(request))


def custom_403_view(request, exception=None):
    """
    Handler personalizado para errores 403 (Forbidden - Acceso denegado).
    NO loguea (ya lo hace el middleware automáticamente).
    """
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'No tienes permiso para acceder a este recurso.',
            'status': 403
        }, status=403)
    
    # Para requests normales: mensaje amigable
    messages.error(request, 'No tienes permisos para acceder a esta página. Si crees que esto es un error, contacta con tu administrador.')
    
    return HttpResponseRedirect(_get_safe_redirect_url(request))


def custom_404_view(request, exception=None):
    """
    Handler personalizado para errores 404 (Not Found - Página no encontrada).
    NO loguea (ya lo hace el middleware automáticamente).
    Solo el 404 muestra un template porque es común y no es un error crítico.
    """
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'El recurso solicitado no existe.',
            'status': 404
        }, status=404)
    
    # Para requests normales: mostrar template de 404 (es la única excepción)
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """
    Handler personalizado para errores 500 (Internal Server Error).
    NO loguea (ya lo hace el middleware automáticamente con traceback completo).
    IMPORTANTE: NO muestra template 500.html, solo notificación y redirección.
    """
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Ocurrió un error inesperado. Por favor, intenta nuevamente.',
            'status': 500
        }, status=500)
    
    # Para requests normales: mensaje amigable y tranquilizador
    try:
        messages.error(
            request, 
            'Algo salió mal de nuestro lado. Ya estamos trabajando en solucionarlo. Por favor, intenta nuevamente en unos momentos.'
        )
    except Exception:
        pass  # Si falla el mensaje, no romper
    
    # Redirigir al dashboard (NO mostrar template 500.html)
    return HttpResponseRedirect(_get_safe_redirect_url(request))
