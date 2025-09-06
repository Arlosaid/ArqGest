"""
Handlers personalizados para errores HTTP en producción.
Estos handlers aseguran que se muestren las páginas de error personalizadas
en lugar de las páginas genéricas de Railway o Django.
"""
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_400_view(request, exception=None):
    """
    Handler personalizado para errores 400 (Bad Request).
    """
    logger.warning(
        '400 Bad Request',
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Solicitud incorrecta',
            'status': 400
        }, status=400)
    
    return render(request, '400.html', status=400)


def custom_403_view(request, exception=None):
    """
    Handler personalizado para errores 403 (Forbidden).
    """
    logger.warning(
        '403 Forbidden',
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Acceso denegado',
            'status': 403
        }, status=403)
    
    return render(request, '403.html', status=403)


def custom_404_view(request, exception=None):
    """
    Handler personalizado para errores 404 (Not Found).
    """
    logger.warning(
        '404 Not Found',
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'referer': request.META.get('HTTP_REFERER', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Página no encontrada',
            'status': 404
        }, status=404)
    
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """
    Handler personalizado para errores 500 (Internal Server Error).
    """
    logger.error(
        '500 Internal Server Error',
        extra={
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # Para requests AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Error interno del servidor',
            'status': 500
        }, status=500)
    
    return render(request, '500.html', status=500)
