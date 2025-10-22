from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint para Railway/Docker.
    Verifica estado de DB, cache y aplicación.
    """
    status = {
        "status": "healthy",
        "checks": {}
    }
    http_status = 200
    
    # Check 1: Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = "error"
        status["status"] = "degraded"
        logger.warning(f"Database health check failed: {str(e)}")
        # No falla completamente si DB tiene problemas temporales
    
    # Check 2: Cache (opcional)
    try:
        cache.set("health_check", "ok", 10)
        cache_result = cache.get("health_check")
        status["checks"]["cache"] = "ok" if cache_result == "ok" else "error"
    except Exception as e:
        status["checks"]["cache"] = "unavailable"
        logger.warning(f"Cache health check failed: {str(e)}")
        # Cache no es crítico
    
    # Check 3: Application
    status["checks"]["application"] = "ok"
    
    return JsonResponse(status, status=http_status)


def readiness_check(request):
    """
    Readiness check más estricto - solo responde OK si todo está listo.
    """
    try:
        # Verificar DB obligatoriamente
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({"status": "ready"}, status=200)
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JsonResponse(
            {"status": "not_ready", "error": str(e)}, 
            status=503
        )


def liveness_check(request):
    """
    Liveness check simple - solo verifica que la app responde.
    """
    return JsonResponse({"status": "alive"}, status=200)
