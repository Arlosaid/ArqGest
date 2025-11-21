# Solución: Archivos grandes no se procesaban correctamente

## Problema Identificado

Al analizar los logs del upload del archivo `WF2025.v14.5.18.12900.ZDescargas.org.rar` (875.97 MB), se encontraron dos problemas críticos:

### 1. Bug de Validación Silenciosa ❌

**Síntoma:**
- El archivo se subía completamente (875.97 MB)
- Pasaba la verificación de storage (can_upload=True)
- Pero `valid_files_count=0` sin ningún mensaje de error al usuario

**Causa Raíz:**
En `arc_manager/apps/files/views.py`, línea 202, cuando `validate_project_file()` lanzaba un `ValidationError`, el código hacía `continue` saltándose toda la lógica que registra y reporta los errores al usuario.

```python
except ValidationError as e:
    file_errors.extend(e.messages)
    log_operation(...)
    continue  # ❌ BUG: Salta el procesamiento de errores
```

Esto causaba que los archivos se rechazaran **silenciosamente** sin informar al usuario por qué.

### 2. Límite de Tamaño Desactualizado

**Configuración Anterior:**
- `max_file_size_mb = 500 MB` (valor de migración antigua)

**Archivo Intentado:**
- 875.97 MB (mayor al límite)

**Resultado:**
- El archivo era rechazado por tamaño, pero debido al bug #1, no se informaba al usuario

## Soluciones Implementadas ✅

### 1. Corrección del Bug de Validación

**Archivo:** `arc_manager/apps/files/views.py`

**Cambio:** Eliminado el `continue` que causaba el bug

```python
except ValidationError as e:
    file_errors.extend(e.messages)
    log_operation(...)
    # NO hacer continue aquí - dejar que file_errors se procese correctamente
```

**Resultado:** Ahora los errores de validación se reportan correctamente al usuario con mensajes claros.

### 2. Actualización del Límite de Tamaño

**Migración:** `0010_update_max_file_size_to_1500mb.py`

**Cambios:**
- Límite actualizado de 500 MB → **1500 MB**
- Respeta configuraciones personalizadas mayores
- Caché limpiado automáticamente

**Verificación:**
```bash
$ docker-compose exec web python manage.py shell -c \
  "from apps.main.models import SystemSettings; s = SystemSettings.load(); \
   print(f'max_file_size_mb: {s.max_file_size_mb} MB')"

max_file_size_mb: 1500 MB ✅
```

## Impacto en Usuarios

### Antes ❌
- Archivos grandes (>500 MB) se rechazaban silenciosamente
- Usuario no recibía feedback sobre por qué fallaba
- Logs mostraban `valid_files_count=0` sin contexto

### Después ✅
- Archivos hasta 1500 MB se pueden subir
- Errores de validación se reportan claramente al usuario
- Logs detallados para debugging

## Ejemplo de Mensaje de Error Correcto

**Antes:**
```json
{"success": false, "valid_files_count": 0}
```

**Ahora:**
```json
{
  "success": false,
  "error": "Archivos no válidos encontrados:\n• archivo.rar: Archivo muy grande (875.9MB, máx: 1500MB)",
  "validation_errors": ["archivo.rar: Archivo muy grande (875.9MB, máx: 1500MB)"],
  "valid_files_count": 0,
  "invalid_files_count": 1
}
```

## Próximos Pasos Recomendados

1. **Monitorear logs de uploads** para verificar que los errores se reporten correctamente
2. **Ajustar límite si es necesario** desde el admin de Django: `/admin/main/systemsettings/`
3. **Usar herramientas de diagnóstico:**
   - `docker-compose exec web python manage.py verify_file_limits` - Verificar límites actuales
   - `docker-compose exec web python scripts/check_large_uploads.py [phase_id]` - Diagnóstico completo
4. **Considerar configurar variables de entorno:**
   - `MAX_FILE_SIZE_MB` - Límite por archivo (default: 1500)
   - `PRESIGN_EXPIRES_SECONDS` - Tiempo de expiración URLs presignadas (default: 7200 = 2 horas)

## Configuración Técnica Actual

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `max_file_size_mb` | 1500 MB | Tamaño máximo por archivo |
| `data_upload_max_memory_mb` | 25 MB | Archivos procesados en memoria |
| `storage_trial_gb` | 10 GB | Límite para planes Trial |
| `storage_basic_gb` | 75 GB | Límite para planes Básico |

## Notas Adicionales

- Los archivos grandes (>25 MB) se procesan mediante streaming para evitar problemas de memoria
- Las URLs presignadas tienen 2 horas de validez para archivos muy grandes
- El sistema soporta subidas directas a R2/S3 para mejor rendimiento

