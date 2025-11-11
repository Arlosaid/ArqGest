from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
import logging
import time

logger = logging.getLogger(__name__)


@csrf_exempt
@never_cache
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
        logger.error(f"Database health check failed after {db_time:.0f}ms: {error_msg}")
    
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
        logger.warning(f"Cache health check failed: {str(e)}")
        # Cache no es crítico, no afecta el status general
    
    # Check 3: Application
    status["checks"]["application"] = {
        "status": "ok",
        "debug_mode": settings.DEBUG
    }
    
    # Tiempo total del healthcheck
    total_time = (time.time() - start_time) * 1000
    status["total_response_time_ms"] = round(total_time, 2)
    
    # Log del resultado (DEBUG para no saturar logs con health checks frecuentes)
    if http_status == 200:
        logger.debug(f"✓ Health check OK ({total_time:.0f}ms)")
    else:
        logger.error(f"✗ Health check FAILED ({total_time:.0f}ms) - returning 503")
    
    return JsonResponse(status, status=http_status)


@csrf_exempt
@never_cache
def readiness_check(request):
    """
    Readiness check completo - verifica que TODO está listo para recibir tráfico.
    
    Este endpoint es usado por Railway para determinar si el deploy fue exitoso.
    Verifica: DB conectada + migraciones aplicadas + cache disponible.
    
    Best practices: Health checks deben ser rápidos (<5s) pero completos.
    """
    # Logging al inicio para debugging
    logger.info("Readiness check initiated")
    
    start_time = time.time()
    checks = {}
    ready = True
    
    # Check 1: Database connection (CRÍTICO)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = {"status": "ready", "critical": True}
        logger.info("Readiness check - DB connection OK")
    except Exception as e:
        checks["database"] = {
            "status": "not_ready",
            "error": str(e)[:200],
            "critical": True
        }
        ready = False
        logger.error(f"Readiness check - DB connection failed: {str(e)}")
    
    # Check 2: Migraciones aplicadas (ADVERTENCIA, no crítico)
    # Nota: Migraciones pendientes son comunes durante desarrollo y no deben bloquear deploys
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            # Hay migraciones pendientes - reportar pero NO fallar
            pending_migrations = [f"{migration[0]}.{migration[1]}" for migration in plan[:3]]
            checks["migrations"] = {
                "status": "pending",
                "pending_count": len(plan),
                "sample": pending_migrations,
                "critical": False  # No crítico - solo advertencia
            }
            logger.warning(f"Readiness check - {len(plan)} pending migrations detected: {pending_migrations}")
        else:
            checks["migrations"] = {"status": "up_to_date", "critical": False}
    except Exception as e:
        checks["migrations"] = {
            "status": "check_failed",
            "error": str(e)[:200],
            "critical": False
        }
        # No fallar por esto - puede ser un problema transitorio
        logger.warning(f"Readiness check - Migration check failed: {str(e)}")
    
    # Check 3: Cache (Redis) disponible (IMPORTANTE pero no crítico)
    try:
        cache.set("readiness_check", "ok", 10)
        cache_result = cache.get("readiness_check")
        if cache_result == "ok":
            checks["cache"] = {"status": "ready", "critical": False}
        else:
            checks["cache"] = {"status": "degraded", "critical": False}
            logger.warning("Readiness check - Cache degraded")
    except Exception as e:
        checks["cache"] = {
            "status": "unavailable",
            "error": str(e)[:100],
            "critical": False
        }
        logger.warning(f"Readiness check - Cache unavailable: {str(e)}")
        # Cache no es crítico, no afecta readiness
    
    # Check 4: Settings y configuración
    try:
        checks["application"] = {
            "status": "ok",
            "debug_mode": settings.DEBUG,
            "critical": True
        }
    except Exception as e:
        checks["application"] = {
            "status": "error",
            "error": str(e)[:100],
            "critical": True
        }
        ready = False
    
    # Calcular tiempo total
    total_time = (time.time() - start_time) * 1000
    
    if ready:
        logger.info(f"✓ Readiness check PASSED ({total_time:.0f}ms) - service ready for traffic")
        return JsonResponse({
            "status": "ready",
            "checks": checks,
            "response_time_ms": round(total_time, 2)
        }, status=200)
    else:
        logger.error(f"✗ Readiness check FAILED ({total_time:.0f}ms) - service NOT ready")
        return JsonResponse({
            "status": "not_ready",
            "checks": checks,
            "response_time_ms": round(total_time, 2)
        }, status=503)


@csrf_exempt
@never_cache
def liveness_check(request):
    """
    Liveness check simple - verifica que la aplicación está viva (no colgada).
    
    Este endpoint NO verifica dependencias externas (DB, cache, etc).
    Solo verifica que Django puede procesar requests.
    
    Uso: Para detectar si el proceso está colgado y necesita reiniciarse.
    Si este endpoint no responde, el contenedor debe reiniciarse.
    """
    return JsonResponse({
        "status": "alive",
        "timestamp": time.time()
    }, status=200)


@csrf_exempt
@never_cache
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
