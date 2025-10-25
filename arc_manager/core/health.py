from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint para Railway/Docker.
    Verifica estado de DB, cache y aplicación.
    Railway usa este endpoint para determinar si el servicio está healthy.
    """
    start_time = time.time()
    status = {
        "status": "healthy",
        "checks": {},
        "timestamp": time.time()
    }
    http_status = 200
    
    # Check 1: Database (CRÍTICO)
    db_start = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_time = (time.time() - db_start) * 1000
        status["checks"]["database"] = {
            "status": "ok",
            "response_time_ms": round(db_time, 2)
        }
    except Exception as e:
        db_time = (time.time() - db_start) * 1000
        error_msg = str(e)
        status["checks"]["database"] = {
            "status": "error",
            "error": error_msg[:200],
            "response_time_ms": round(db_time, 2)
        }
        status["status"] = "unhealthy"
        http_status = 503  # Service Unavailable
        logger.error(f"❌ Database health check failed after {db_time:.0f}ms: {error_msg}")
    
    # Check 2: Cache (opcional, no crítico)
    try:
        cache.set("health_check", "ok", 10)
        cache_result = cache.get("health_check")
        status["checks"]["cache"] = {
            "status": "ok" if cache_result == "ok" else "degraded"
        }
    except Exception as e:
        status["checks"]["cache"] = {
            "status": "unavailable",
            "error": str(e)[:100]
        }
        logger.warning(f"⚠️  Cache health check failed: {str(e)}")
        # Cache no es crítico, no afecta el status general
    
    # Check 3: Application
    status["checks"]["application"] = {
        "status": "ok",
        "debug_mode": settings.DEBUG
    }
    
    # Tiempo total del healthcheck
    total_time = (time.time() - start_time) * 1000
    status["total_response_time_ms"] = round(total_time, 2)
    
    # Log del resultado
    if http_status == 200:
        logger.info(f"✓ Health check OK ({total_time:.0f}ms)")
    else:
        logger.error(f"✗ Health check FAILED ({total_time:.0f}ms) - returning 503")
    
    return JsonResponse(status, status=http_status)


def readiness_check(request):
    """
    Readiness check más estricto - solo responde OK si todo está listo.
    Railway puede usar esto para determinar cuándo empezar a enviar tráfico.
    """
    checks = {}
    ready = True
    
    # Check DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = f"not_ready: {str(e)[:100]}"
        ready = False
        logger.error(f"❌ Readiness check - DB not ready: {str(e)}")
    
    # Check Django está configurado
    try:
        checks["settings"] = "ok"
        checks["debug_mode"] = settings.DEBUG
    except Exception as e:
        checks["settings"] = f"error: {str(e)[:100]}"
        ready = False
    
    if ready:
        logger.info("✓ Readiness check PASSED - service ready")
        return JsonResponse({
            "status": "ready",
            "checks": checks
        }, status=200)
    else:
        logger.error("✗ Readiness check FAILED - service not ready")
        return JsonResponse({
            "status": "not_ready",
            "checks": checks
        }, status=503)


def liveness_check(request):
    """
    Liveness check simple - solo verifica que la app responde.
    """
    return JsonResponse({"status": "alive"}, status=200)


def database_diagnostic(request):
    """
    Endpoint de diagnóstico detallado de la base de datos.
    Solo accesible en desarrollo o con parámetro secreto.
    URL: /health/db-diagnostic/?secret=tu_secreto
    """
    import os
    from django.db import connections
    from django.db.utils import OperationalError
    
    # Seguridad: solo en debug o con secreto
    secret = request.GET.get('secret', '')
    expected_secret = os.environ.get('DIAGNOSTIC_SECRET', 'dev_secret_123')
    
    if not settings.DEBUG and secret != expected_secret:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    diagnostic = {
        "timestamp": time.time(),
        "environment": os.environ.get('RAILWAY_ENVIRONMENT', 'unknown'),
        "database_config": {},
        "connection_test": {},
        "environment_vars": {}
    }
    
    # 1. Configuración de DB desde settings
    db_settings = settings.DATABASES.get('default', {})
    diagnostic["database_config"] = {
        "ENGINE": db_settings.get('ENGINE', 'not set'),
        "NAME": db_settings.get('NAME', 'not set'),
        "HOST": db_settings.get('HOST', 'not set')[:20] + '...' if db_settings.get('HOST') else 'not set',
        "PORT": db_settings.get('PORT', 'not set'),
        "USER": db_settings.get('USER', 'not set'),
        "OPTIONS": list(db_settings.get('OPTIONS', {}).keys())
    }
    
    # 2. Variables de entorno relacionadas con DB
    db_env_vars = ['DATABASE_URL', 'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER']
    for var in db_env_vars:
        value = os.environ.get(var, 'not set')
        if var == 'DATABASE_URL' and value != 'not set':
            # Ofuscar credenciales
            value = value.split('@')[1] if '@' in value else 'malformed'
        diagnostic["environment_vars"][var] = value
    
    # 3. Test de conexión detallado
    try:
        conn = connections['default']
        with conn.cursor() as cursor:
            # Test básico
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # Información de la BD
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            
            # Información de usuario actual
            cursor.execute("SELECT current_user, current_database()")
            user_info = cursor.fetchone()
            
            diagnostic["connection_test"] = {
                "status": "SUCCESS",
                "database_version": db_version[:100],
                "current_user": user_info[0],
                "current_database": user_info[1],
                "connection_successful": True
            }
            
    except OperationalError as e:
        diagnostic["connection_test"] = {
            "status": "FAILED",
            "error_type": "OperationalError",
            "error_message": str(e)[:500],
            "connection_successful": False,
            "possible_causes": [
                "Database service not running",
                "Incorrect credentials",
                "Network connectivity issue",
                "Database not created yet"
            ]
        }
    except Exception as e:
        diagnostic["connection_test"] = {
            "status": "FAILED",
            "error_type": type(e).__name__,
            "error_message": str(e)[:500],
            "connection_successful": False
        }
    
    # Status HTTP según el resultado
    http_status = 200 if diagnostic["connection_test"].get("connection_successful") else 500
    
    return JsonResponse(diagnostic, status=http_status, json_dumps_params={'indent': 2})
