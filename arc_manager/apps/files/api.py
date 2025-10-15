# apps/files/api.py
"""
API optimizada para uploads masivos con tracking de progreso
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def upload_progress(request, upload_id):
    """
    API para obtener progreso de upload en tiempo real
    """
    try:
        progress_data = cache.get(f"upload_progress_{upload_id}")
        
        if not progress_data:
            return JsonResponse({
                'status': 'not_found',
                'message': 'Upload ID no encontrado'
            }, status=404)
        
        # Calcular estadísticas adicionales
        if 'start_time' in progress_data:
            import time
            elapsed = time.time() - progress_data['start_time']
            
            if progress_data.get('progress', 0) > 0:
                estimated_total = (elapsed * 100) / progress_data['progress']
                remaining = max(0, estimated_total - elapsed)
                
                progress_data.update({
                    'elapsed_seconds': round(elapsed, 1),
                    'estimated_remaining_seconds': round(remaining, 1),
                    'speed_mbps': round((progress_data.get('size', 0) * progress_data.get('progress', 0) / 100) / (1024 * 1024 * elapsed), 2) if elapsed > 0 else 0
                })
        
        return JsonResponse({
            'status': 'success',
            'data': progress_data
        })
        
    except Exception as e:
        logger.error(f"Error getting upload progress: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error interno del servidor'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_upload_progress(request, upload_id):
    """
    API para actualizar progreso de upload (usado por frontend)
    """
    try:
        data = json.loads(request.body)
        progress = data.get('progress', 0)
        status = data.get('status', 'uploading')
        
        # Validar progreso
        if not 0 <= progress <= 100:
            return JsonResponse({
                'status': 'error',
                'message': 'Progreso debe estar entre 0 y 100'
            }, status=400)
        
        # Obtener datos existentes
        existing_data = cache.get(f"upload_progress_{upload_id}", {})
        
        # Actualizar datos
        import time
        existing_data.update({
            'progress': progress,
            'status': status,
            'last_update': time.time()
        })
        
        # Guardar en caché
        cache.set(f"upload_progress_{upload_id}", existing_data, timeout=3600)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Progreso actualizado'
        })
        
    except Exception as e:
        logger.error(f"Error updating upload progress: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error interno del servidor'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def r2_health_check(request):
    """
    API para verificar salud de R2
    """
    try:
        from core.r2_config import R2HealthCheck
        
        # Ejecutar health check completo
        result = R2HealthCheck.full_health_check()
        
        return JsonResponse({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in R2 health check: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def upload_stats(request):
    """
    API para estadísticas de uploads del usuario
    """
    try:
        from apps.files.models import ProjectFile
        from django.utils import timezone
        from datetime import timedelta
        
        # Estadísticas del usuario en los últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        user_files = ProjectFile.objects.filter(
            uploaded_by=request.user,
            uploaded_at__gte=thirty_days_ago
        )
        
        stats = {
            'total_files': user_files.count(),
            'total_size_mb': round(sum(f.size_bytes for f in user_files) / (1024 * 1024), 2),
            'large_files_count': user_files.filter(size_bytes__gte=100*1024*1024).count(),
            'avg_file_size_mb': 0,
            'most_common_extensions': [],
            'upload_trend': []
        }
        
        if stats['total_files'] > 0:
            stats['avg_file_size_mb'] = round(stats['total_size_mb'] / stats['total_files'], 2)
            
            # Extensiones más comunes
            from django.db.models import Count
            extensions = user_files.values('ext_upper').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            stats['most_common_extensions'] = [
                {'extension': ext['ext_upper'], 'count': ext['count']}
                for ext in extensions
            ]
            
            # Tendencia de uploads (últimos 7 días)
            for i in range(7):
                date = timezone.now().date() - timedelta(days=i)
                day_files = user_files.filter(uploaded_at__date=date)
                stats['upload_trend'].append({
                    'date': date.isoformat(),
                    'files': day_files.count(),
                    'size_mb': round(sum(f.size_bytes for f in day_files) / (1024 * 1024), 2)
                })
            
            stats['upload_trend'].reverse()  # Orden cronológico
        
        return JsonResponse({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting upload stats: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error interno del servidor'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def optimize_upload_settings(request):
    """
    API para optimizar configuración de upload basada en el contexto del usuario
    """
    try:
        data = json.loads(request.body)
        connection_type = data.get('connection_type', 'broadband')  # broadband, mobile, slow
        device_type = data.get('device_type', 'desktop')  # desktop, tablet, mobile
        
        # Configuración optimizada basada en contexto
        if connection_type == 'mobile' or device_type == 'mobile':
            config = {
                'chunk_size_mb': 10,  # Chunks más pequeños para móvil
                'max_concurrent_uploads': 2,  # Menos concurrencia
                'retry_attempts': 5,  # Más retries para conexiones inestables
                'timeout_minutes': 45,  # Timeout más largo
                'recommended_max_file_size_mb': 200
            }
        elif connection_type == 'slow':
            config = {
                'chunk_size_mb': 5,  # Chunks muy pequeños
                'max_concurrent_uploads': 1,  # Sin concurrencia
                'retry_attempts': 8,  # Muchos retries
                'timeout_minutes': 60,  # Timeout muy largo
                'recommended_max_file_size_mb': 100
            }
        else:  # broadband/desktop
            config = {
                'chunk_size_mb': 50,  # Chunks grandes para máxima velocidad
                'max_concurrent_uploads': 15,  # Máxima concurrencia
                'retry_attempts': 3,  # Pocos retries necesarios
                'timeout_minutes': 30,  # Timeout estándar
                'recommended_max_file_size_mb': 1200
            }
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'optimized_config': config,
                'detected_context': {
                    'connection_type': connection_type,
                    'device_type': device_type
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error optimizing upload settings: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error interno del servidor'
        }, status=500)
