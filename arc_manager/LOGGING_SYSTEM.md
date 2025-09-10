# 📊 Sistema de Logging Estructurado - ARC Manager (OPTIMIZADO)

## 🎯 Resumen

Hemos implementado y **OPTIMIZADO** un sistema completo de logging estructurado que captura **TODOS** los errores 500, errores de aplicación, eventos de seguridad y métricas de rendimiento con **414 códigos de error específicos** distribuidos en **8 categorías** para facilitar el monitoreo y troubleshooting avanzado.

## 🏗️ Arquitectura del Sistema

### 1. **Códigos de Error Estructurados**
Ubicación: `core/error_codes.py`

Cada módulo tiene códigos únicos organizados en **8 categorías principales**:
- **Tasks (T001-T999)**: 64 códigos - T001=título faltante, T111=transición inválida, T501=tiempo inválido, etc.
- **Projects (P001-P999)**: 65 códigos - P001=nombre duplicado, P301=fase duplicada, P601=error reporte, etc.
- **Users (U001-U999)**: 68 códigos - U001=email duplicado, U301=contraseña actual inválida, U601=eliminar denegado, etc.
- **Organizations (O001-O999)**: 33 códigos - O001=nombre duplicado, O101=límite plan, O301=eliminar denegado, etc.
- **Files (F001-F999)**: 41 códigos - F001=archivo muy grande, F201=error conversión, F401=conflicto sync, etc.
- **Authentication (A001-A999)**: 44 códigos - A001=email existe, A301=2FA inválido, A501=token inválido, etc.
- **Plans (PL001-PL999)**: 35 códigos - PL001=error pago, PL201=facturación fallida, PL301=características inválidas, etc.
- **System (S001-S999)**: 64 códigos - S001=error BD, S501=ataque fuerza bruta, S901=rendimiento crítico, etc.

### 2. **Middlewares de Logging**
Ubicación: `core/logging_middleware.py`

- **Enhanced500LoggingMiddleware**: Captura TODOS los errores 500 con contexto completo
- **DatabaseErrorLoggingMiddleware**: Errores específicos de base de datos
- **PerformanceLoggingMiddleware**: Requests lentas (>2 segundos)

### 3. **Helper Functions (OPTIMIZADAS)**
```python
from core.error_codes import (
    log_operation, log_operation_with_context, log_performance_warning, log_security_event,
    get_all_error_codes, get_error_codes_by_category, is_critical_error, 
    format_error_for_monitoring
)

# Logging básico
log_operation('CREATE_TASK', user.email, logger, level='INFO', task_id=123)

# Con código de error específico
log_operation('CREATE_TASK_ERROR', user.email, logger, level='ERROR', 
              error_code=TaskErrorCodes.TASK_UPDATE_STATUS_TRANSITION_INVALID,
              task_id=123, current_status='IN_PROGRESS', attempted_status='COMPLETED')

# Con contexto automático de request
log_operation_with_context('USER_UPDATE', user.email, logger, request=request,
                           level='INFO', user_id=456)

# Performance
log_performance_warning('SLOW_QUERY', user.email, logger, duration_ms=3500)

# Security  
log_security_event('BRUTE_FORCE_ATTACK', 'anonymous', logger, ip_address='1.2.3.4',
                   failed_attempts=10)

# Utilidades de análisis
total_codes = len(get_all_error_codes())  # 414 códigos
task_codes = get_error_codes_by_category('TASK')  # 64 códigos de tareas
is_critical = is_critical_error('S501')  # True para errores críticos
monitor_data = format_error_for_monitoring('S502', {'ip': '1.2.3.4'})
```

## 📋 Formatos de Log

### ✅ Logs Exitosos
```
INFO OP [CREATE_TASK] User: user@example.com task_id: 123 project_id: 45 title: Nueva tarea
```

### ❌ Logs de Error
```
ERROR OP [CREATE_TASK_ERROR] User: user@example.com project_id: 45 error_code: T001 ERROR_CODE: T001
```

### 🐌 Logs de Rendimiento
```
WARNING OP [SLOW_QUERY] User: user@example.com duration_ms: 3500.0 path: /projects/123/ ERROR_CODE: PERF_SLOW_QUERY
```

### 🚨 Errores 500 (Middleware)
```
ERROR OP [HTTP_500_ERROR] User: user@example.com path: /projects/tasks/40/edit/ method: GET client_ip: 127.0.0.1 exception_type: ValueError exception_message: Invalid form parameter ERROR_CODE: S203
```

## 🔍 Monitoreo y Alertas

### En Desarrollo (Docker Local)
```bash
# Ver todos los errores con códigos
tail -f arc_manager/logs/errors.log | grep ERROR_CODE

# Filtrar por tipo de error
tail -f arc_manager/logs/errors.log | grep "ERROR_CODE: T"  # Solo tareas
tail -f arc_manager/logs/errors.log | grep "ERROR_CODE: S"  # Solo sistema

# Ver errores 500 específicamente
tail -f arc_manager/logs/errors.log | grep "HTTP_500_ERROR"

# Performance issues
tail -f arc_manager/logs/errors.log | grep "PERF_"
```

### En Producción (Railway)
1. **Dashboard de Railway**: Los logs aparecen en tiempo real
2. **Alertas por código**: Configurar alertas cuando aparezcan códigos específicos
3. **Métricas**: Contar errores por código para identificar patrones

### Ejemplos de Queries para Monitoreo
```bash
# Errores más frecuentes
grep "ERROR_CODE:" logs/errors.log | cut -d' ' -f-10 | sort | uniq -c | sort -nr

# Usuarios con más errores
grep "ERROR_CODE:" logs/errors.log | grep -o "User: [^[:space:]]*" | sort | uniq -c | sort -nr

# Errores por hora
grep "ERROR_CODE:" logs/errors.log | cut -d' ' -f1-2 | cut -d':' -f1-2 | sort | uniq -c
```

## 🧪 Testing del Sistema

### Ejecutar Tests de Logging
```bash
cd arc_manager
python manage.py shell < test_logging.py
```

### Generar Error 500 de Prueba
1. Acceder a: `http://localhost:8000/projects/tasks/40/edit/`
2. Revisar logs: `tail -f arc_manager/logs/errors.log`
3. Buscar: `HTTP_500_ERROR` con `ERROR_CODE: S203`

## 📊 Códigos de Error por Módulo

### Tasks (T001-T999)
- `T001`: Título faltante en creación
- `T002`: Fase faltante en creación
- `T003`: Fase no encontrada
- `T004`: Usuario asignado inválido
- `T101`: Tarea no encontrada en actualización
- `T102`: Estado inválido
- `T201`: Error en eliminación
- `T901`: Consulta lenta (>2s)
- `T902`: Dataset grande (>1000 registros)

### Projects (P001-P999)
- `P001`: Nombre duplicado
- `P002`: Plantilla inválida
- `P003`: Error en creación de fases
- `P101`: Proyecto no encontrado

### Users (U001-U999)
- `U001`: Email duplicado
- `U002`: Email inválido
- `U003`: Contraseña débil
- `U201`: Credenciales inválidas
- `U202`: Cuenta bloqueada

### Files (F001-F999)
- `F001`: Archivo muy grande
- `F002`: Tipo no permitido
- `F003`: Error de almacenamiento
- `F101`: Archivo no encontrado
- `F102`: Sin permisos de descarga

### System (S001-S999)
- `S001`: Error de conexión a BD
- `S002`: Timeout de BD
- `S003`: Error de integridad de BD
- `S101`: Error de cache
- `S201`: Error de autenticación middleware
- `S202`: Error de permisos middleware
- `S203`: Error inesperado middleware

## 🚀 Beneficios del Sistema

### Para Desarrollo
- **Debugging rápido**: Códigos específicos para cada tipo de error
- **Contexto completo**: Usuario, IP, parámetros, stack trace
- **Trazabilidad**: Seguimiento completo de operaciones

### Para Producción
- **Alertas automáticas**: Configurar alertas por código de error
- **Métricas**: Contadores de errores por tipo
- **Análisis de tendencias**: Identificar patrones de errores
- **SLA monitoring**: Detectar degradación de servicio

### Para Soporte
- **Información completa**: Todos los datos necesarios en un log
- **Búsqueda eficiente**: Filtrar por código, usuario, o tipo de error
- **Resolución rápida**: Contexto suficiente para reproducir problemas

## 🔧 Configuración Adicional

### Variables de Entorno Recomendadas
```bash
# En .env para desarrollo
LOG_LEVEL=DEBUG
LOG_TO_FILE=true

# En Railway para producción
LOG_LEVEL=INFO
LOG_TO_FILE=true
ENABLE_PERFORMANCE_LOGGING=true
```

### Configuración de Alertas (Railway)
1. Configurar webhook para códigos críticos: `S001`, `S002`, `S003`
2. Alertas de rendimiento: `PERF_SLOW_QUERY`, `PERF_SLOW_REQUEST`
3. Alertas de seguridad: `SECURITY_*`

## 📈 Próximos Pasos

1. **Métricas en Dashboard**: Integrar con Grafana/DataDog
2. **Alertas Slack/Email**: Notificaciones automáticas
3. **Análisis ML**: Detección de anomalías en patrones de error
4. **Health Checks**: Endpoints de salud basados en códigos de error

---

**🎯 Con este sistema, ahora tienes visibilidad completa de todos los errores 500 y eventos del sistema, tanto en desarrollo como en producción.**
