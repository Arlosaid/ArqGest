"""
Handlers personalizados para errores HTTP.
En lugar de mostrar páginas de error completas, usa el sistema de notificaciones
de la app para mostrar mensajes amigables al usuario.
Los detalles técnicos solo van a los logs del backend.
"""
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from core.structured_logging import log_error, log_security_event

logger = logging.getLogger(__name__)


def custom_400_view(request, exception=None):
    """
    Handler personalizado para errores 400 (Bad Request).
    """
    # Log técnico para backend (con detalles)
    log_error(
        event="http_400_bad_request",
        error_code="HTTP400",
        error_message="Bad Request",
        path=request.path,
        method=request.method,
        user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        logger_name='django.request'
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'La solicitud no pudo procesarse. Por favor, intenta nuevamente.',
            'status': 400
        }, status=400)
    
    # Para requests normales: mensaje amigable y redirigir al inicio o página anterior
    messages.warning(request, 'La información enviada no es válida. Por favor, verifica e intenta nuevamente.')
    
    # Intentar redirigir a la página anterior, si no existe ir al dashboard
    referer = request.META.get('HTTP_REFERER')
    if referer and request.build_absolute_uri() != referer:
        return redirect(referer)
    return redirect('dashboard')


def custom_403_view(request, exception=None):
    """
    Handler personalizado para errores 403 (Forbidden - Acceso denegado).
    """
    # Log técnico para backend (puede indicar intento de ataque)
    log_security_event(
        event="http_403_forbidden",
        severity="medium",
        path=request.path,
        method=request.method,
        user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        logger_name='django.security'
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'No tienes permiso para acceder a este recurso.',
            'status': 403
        }, status=403)
    
    # Para requests normales: mensaje amigable
    messages.error(request, 'No tienes permisos para acceder a esta página. Si crees que esto es un error, contacta con tu administrador.')
    
    # Redirigir a la página anterior o al dashboard
    referer = request.META.get('HTTP_REFERER')
    if referer and request.build_absolute_uri() != referer:
        return redirect(referer)
    return redirect('dashboard')


def custom_404_view(request, exception=None):
    """
    Handler personalizado para errores 404 (Not Found - Página no encontrada).
    """
    # Log técnico para backend (solo WARNING, no es crítico)
    logger.warning(
        f'404 Not Found: {request.path}',
        extra={
            'path': request.path,
            'method': request.method,
            'referer': request.META.get('HTTP_REFERER', ''),
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'El recurso solicitado no existe.',
            'status': 404
        }, status=404)
    
    # Para requests normales: mostrar template de 404
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """
    Handler personalizado para errores 500 (Internal Server Error).
    Este es el más importante: no asustar al usuario, pero loguear todo para los devs.
    """
    # Log técnico COMPLETO para backend (ERROR crítico con traceback)
    log_error(
        event="http_500_internal_error",
        error_code="HTTP500",
        error_message="Internal Server Error",
        path=request.path,
        method=request.method,
        user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        logger_name='django.request'
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Ocurrió un error inesperado. Por favor, intenta nuevamente.',
            'status': 500
        }, status=500)
    
    # Para requests normales: mensaje amigable y tranquilizador
    messages.error(
        request, 
        'Algo salió mal de nuestro lado. Ya estamos trabajando en solucionarlo. Por favor, intenta nuevamente en unos momentos.'
    )
    
    # Redirigir al dashboard (no queremos que el usuario vea una página en blanco)
    return redirect('dashboard')
