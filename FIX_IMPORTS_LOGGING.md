# 🔧 Fix Imports de log_operation - URGENTE

## ❌ Error Actual
```
ImportError: cannot import name 'log_operation' from 'core.error_codes'
```

## 📋 Archivos que Requieren Actualización

### ✅ COMPLETADOS
1. `apps/accounts/middleware.py` - ✅ FIXED
2. `apps/users/views.py` - ✅ FIXED

### ⚠️ PENDIENTES (comentados temporalmente para que arranque)
3. `apps/projects/views.py` - línea 1415
4. `apps/files/views.py` - línea 12
5. `apps/files/security.py` - línea 172  
6. `apps/files/models.py` - líneas 147, 242
7. `apps/orgs/models.py` - líneas 215, 258

## 🔄 Reemplazo Necesario

### ANTES (Incorrecto)
```python
from core.error_codes import log_operation, log_operation_with_context
# ...
log_operation(
    'OPERATION_NAME',
    user_email,
    logger,
    level='ERROR',
    error_code=ErrorCode.CODE,
    **kwargs
)
```

### AHORA (Correcto)
```python
from core.structured_logging import log_error, log_business_event
# ...
log_error(
    event="operation_name",
    error_code=ErrorCode.CODE,
    error_message="descripción",
    **kwargs  # user_email se anonimiza automáticamente
)
```

## ⚡ Solución Rápida Aplicada

He comentado temporalmente las líneas problemáticas con `# FIXME:` para que la app arranque.

**IMPORTANTE:** Estos archivos necesitan ser revisados y actualizados para usar `structured_logging`.

## 📝 TODO para después del deploy

Actualizar cada archivo pendiente siguiendo el patrón:
1. Cambiar import: `from core.structured_logging import log_error, log_business_event`
2. Reemplazar llamadas a `log_operation()` con `log_error()` o `log_business_event()`
3. Ajustar parámetros al nuevo formato

## 🎯 Prioridad

**ALTA:** Los archivos de `files` y `orgs` son críticos para el funcionamiento normal.

Revisar después del deploy inicial.
