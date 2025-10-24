from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)


def server_error_view(request):
    """
    Vista personalizada para errores 500.
    Muestra una notificación amigable usando el sistema de notificaciones moderno.
    """
    # Log del error para debugging
    logger.error(f"Error 500 en {request.path} - Usuario: {getattr(request, 'user', 'Anónimo')}")
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': True,
            'message': 'Ocurrió un error interno. Por favor, inténtalo de nuevo más tarde.',
            'code': 500
        }, status=500)
    
    # Para peticiones normales, mostrar página con notificación usando JavaScript
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error del Servidor - ArqGest</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8f9fa;
                color: #333;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                max-width: 400px;
            }
            .loading {
                font-size: 1.2rem;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="loading">Redirigiendo...</div>
        </div>
        
        <!-- Cargar sistema de notificaciones -->
        <script src="/static/js/notifications.js"></script>
        <script>
            // Mostrar notificación de error y redirigir
            setTimeout(() => {
                if (window.notifications) {
                    window.notifications.error('Ocurrió un error interno. Por favor, inténtalo de nuevo más tarde.', {
                        duration: 8000,
                        persistent: false
                    });
                }
                
                // Redirigir después de mostrar la notificación
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            }, 100);
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content, status=500)


def bad_request_view(request, exception=None):
    """
    Vista personalizada para errores 400.
    Muestra una notificación amigable usando el sistema de notificaciones moderno.
    """
    logger.warning(f"Error 400 en {request.path} - Usuario: {getattr(request, 'user', 'Anónimo')}")
    
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': True,
            'message': 'Solicitud incorrecta. Por favor, verifica los datos enviados.',
            'code': 400
        }, status=400)
    
    # Para peticiones normales, mostrar página con notificación
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error de Solicitud - ArqGest</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8f9fa;
                color: #333;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                max-width: 400px;
            }
            .loading {
                font-size: 1.2rem;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="loading">Redirigiendo...</div>
        </div>
        
        <script src="/static/js/notifications.js"></script>
        <script>
            setTimeout(() => {
                if (window.notifications) {
                    window.notifications.warning('Solicitud incorrecta. Por favor, verifica los datos enviados.', {
                        duration: 6000,
                        persistent: false
                    });
                }
                
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            }, 100);
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content, status=400)


def permission_denied_view(request, exception=None):
    """
    Vista personalizada para errores 403.
    Muestra una notificación amigable usando el sistema de notificaciones moderno.
    """
    logger.warning(f"Error 403 en {request.path} - Usuario: {getattr(request, 'user', 'Anónimo')}")
    
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': True,
            'message': 'No tienes permisos para acceder a este recurso.',
            'code': 403
        }, status=403)
    
    # Para peticiones normales, mostrar página con notificación
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Acceso Denegado - ArqGest</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8f9fa;
                color: #333;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                max-width: 400px;
            }
            .loading {
                font-size: 1.2rem;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="loading">Redirigiendo...</div>
        </div>
        
        <script src="/static/js/notifications.js"></script>
        <script>
            setTimeout(() => {
                if (window.notifications) {
                    window.notifications.warning('No tienes permisos para acceder a este recurso.', {
                        duration: 6000,
                        persistent: false
                    });
                }
                
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            }, 100);
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content, status=403)


def page_not_found_view(request, exception=None):
    """
    Vista personalizada para errores 404.
    Mantiene el template actual ya que es apropiado para este tipo de error.
    """
    logger.info(f"Error 404 en {request.path} - Usuario: {getattr(request, 'user', 'Anónimo')}")
    
    # Para 404, usar el template personalizado existente
    return render(request, '404.html', status=404)
