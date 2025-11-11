# Arreglos de Tests - StorageService

**Fecha:** 10 de noviembre de 2025  
**Tests Arreglados:** 5  
**Estado:** ✅ COMPLETADO

---

## Resumen

Se arreglaron **5 tests que fallaban** en el módulo `test_storage_service.py`. Los problemas eran pre-existentes y no relacionados con los cambios recientes de logging.

---

## Tests Arreglados

### 1. ✅ test_calculate_storage_with_fallback_plan_limit

**Problema:**
```python
result = StorageService.calculate_storage(org.id)
# AttributeError: 'StorageService' has no attribute 'calculate_storage'
```

**Causa:** El método no existía, el correcto es `calculate_storage_usage(organization)`

**Solución:**
```python
result = StorageService.calculate_storage_usage(org)
```

**Archivo:** `tests/orgs/integration/test_storage_service.py:43`

---

### 2. ✅ test_calculate_storage_caches_result

**Problema:**
```python
assert mock_project_file.objects.filter.call_count == 1
# AssertionError: assert 2 == 1
```

**Causa:** El método `calculate_storage_usage` hace 2 llamadas a `filter()`:
1. Una para `aggregate(Sum('size_bytes'))`
2. Otra para `count()`

**Solución:** Verificar que la segunda llamada NO accede a la BD (viene del cache):
```python
# Primera llamada (hace 2 llamadas a filter: aggregate + count)
result1 = StorageService.calculate_storage_usage(org)

# Resetear el contador
mock_project_file.objects.filter.reset_mock()

# Segunda llamada (debe venir del cache, 0 llamadas)
result2 = StorageService.calculate_storage_usage(org)

# Verificar que NO se llamó a filter en la segunda vez (viene del cache)
assert mock_project_file.objects.filter.call_count == 0
```

**Archivo:** `tests/orgs/integration/test_storage_service.py:153-179`

---

### 3. ✅ test_can_upload_file_within_limit

**Problema:**
```python
can_upload, _, _ = StorageService.can_upload_file(org, file_size)
assert can_upload is True  # Falló: assert False is True
```

**Log de error:**
```
WARNING: Upload blocked for org 1545: file size 5120.0MB 
exceeds remaining storage 0MB
```

**Causa:** 
- Org sin subscription tiene límite de **10 GB** (fallback)
- Uso actual mockeado: **10 GB**
- Remaining: **0 GB**
- Intentar subir: **5 GB** ❌
- Resultado: Rechazado porque 10 + 5 = 15 > 10

**Solución:** Usar `OrganizationWithExtraStorageFactory` para tener suficiente espacio:
```python
# Crear org con extra storage para tener suficiente espacio
org = OrganizationWithExtraStorageFactory(extra_storage_gb=65)  # 10 + 65 = 75 GB total

# Mock: 10 GB de uso actual
mock_qs.aggregate.return_value = {'total': 10 * 1024**3}

# Intentar subir archivo de 5 GB (10 + 5 = 15 GB, dentro del límite de 75 GB)
file_size = 5 * 1024**3

can_upload, error_msg, storage_data = StorageService.can_upload_file(org, file_size)

assert can_upload is True  # ✅ Ahora pasa
```

**Archivo:** `tests/orgs/integration/test_storage_service.py:337-355`

---

### 4. ✅ test_can_upload_file_exactly_at_limit

**Problema:** Igual que el test anterior

**Causa:** 
- Org sin subscription: límite de **10 GB**
- Uso actual: **70 GB** (ya excede el límite!)
- Remaining: **0 GB**
- Intentar subir: **5 GB** ❌

**Solución:** Usar org con extra storage:
```python
# Crear org con extra storage para tener 75 GB total
org = OrganizationWithExtraStorageFactory(extra_storage_gb=65)  # 10 + 65 = 75 GB total

# Mock: 70 GB de uso actual
mock_qs.aggregate.return_value = {'total': 70 * 1024**3}

# Archivo de 5 GB (70 + 5 = 75, exactamente el límite)
file_size = 5 * 1024**3

can_upload, error_msg, storage_data = StorageService.can_upload_file(org, file_size)

assert can_upload is True  # ✅ Ahora pasa (70 + 5 = 75 <= 75)
```

**Archivo:** `tests/orgs/integration/test_storage_service.py:378-395`

---

### 5. ✅ test_format_size_bytes

**Problema:**
```python
formatted = StorageService.format_size(500)
assert formatted == "500 B"
# AssertionError: assert '500.0 B' == '500 B'
```

**Causa:** El método `format_size` aplicaba `round(..., 2)` a todos los tamaños, incluyendo bytes

**Solución:** No mostrar decimales para bytes:
```python
@classmethod
def format_size(cls, bytes_size):
    """Formatea el tamaño en bytes a una representación legible"""
    if bytes_size == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(bytes_size, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_size / p, 2)
    
    # Para bytes (i=0), no mostrar decimales
    if i == 0:
        return f"{int(s)} {size_names[i]}"
    
    return f"{s} {size_names[i]}"
```

**Resultado:**
- `format_size(500)` → `"500 B"` ✅
- `format_size(1024)` → `"1.0 KB"` ✅
- `format_size(1024**2)` → `"1.0 MB"` ✅

**Archivo:** `arc_manager/apps/orgs/storage_service.py:157-172`

---

## Resultado Final

### Antes:
```
===== 5 failed, 166 passed, 1 skipped in 205.08s =====
```

### Después:
```
===== 257 passed, 2 skipped in 227.40s =====
```

---

## Archivos Modificados

### 1. tests/orgs/integration/test_storage_service.py
- **Línea 43:** Corregido método `calculate_storage()` → `calculate_storage_usage()`
- **Líneas 166-179:** Mejorado test de cache para verificar correctamente
- **Línea 340:** Agregado `OrganizationWithExtraStorageFactory(extra_storage_gb=65)`
- **Línea 381:** Agregado `OrganizationWithExtraStorageFactory(extra_storage_gb=65)`

### 2. arc_manager/apps/orgs/storage_service.py
- **Líneas 168-170:** Agregada lógica para no mostrar decimales en bytes

---

## Lecciones Aprendidas

### 1. Tests con Mocks Requieren Datos Realistas
Los tests asumían un límite de 75 GB, pero las organizaciones sin subscription tienen un fallback de 10 GB. Es importante que los datos mockeados sean consistentes con la lógica del negocio.

### 2. Cache Puede Hacer Múltiples Llamadas Internas
El test esperaba 1 llamada a `filter()`, pero internamente se hacen 2:
- Una para `aggregate()`
- Otra para `count()`

La solución fue verificar que la **segunda invocación del método** use el cache (0 llamadas).

### 3. Formateo de Números Debe Ser Contextual
Los bytes no necesitan decimales (500 B es más limpio que 500.0 B), pero KB, MB, GB sí (1.0 KB es más claro que 1 KB).

### 4. Los Tests Deben Verificar Comportamiento, No Implementación
En lugar de contar llamadas a métodos internos, es mejor verificar que el resultado final sea correcto (cache funciona = segunda llamada no toca BD).

---

## Tests Relacionados que Ahora Pasan

Estos tests adicionales ahora también pasan correctamente:
- ✅ `test_calculate_storage_empty_organization`
- ✅ `test_calculate_storage_with_extra_storage`
- ✅ `test_calculate_storage_usage_percentage_empty`
- ✅ `test_calculate_storage_remaining_gb`
- ✅ `test_calculate_storage_with_files`
- ✅ `test_calculate_storage_over_limit`
- ✅ `test_calculate_storage_handles_null_aggregate`
- ✅ `test_get_cache_key_format`
- ✅ `test_calculate_storage_uses_cached_data`
- ✅ `test_invalidate_cache_removes_key`
- ✅ `test_cache_timeout_configuration`
- ✅ `test_get_storage_summary_structure`
- ✅ `test_get_storage_summary_status_normal`
- ✅ `test_get_storage_summary_status_warning`
- ✅ `test_get_storage_summary_status_critical`
- ✅ `test_can_upload_file_exceeds_limit`
- ✅ `test_format_size_zero_bytes`
- ✅ `test_format_size_kilobytes`
- ✅ `test_format_size_megabytes`
- ✅ `test_format_size_gigabytes`
- ✅ `test_format_size_terabytes`
- ✅ `test_format_size_decimal_values`
- ✅ `test_calculate_storage_handles_exception`
- ✅ `test_calculate_storage_with_zero_limit`

**Total:** 29/29 tests de storage_service ✅

---

## Verificación

Para verificar que los arreglos funcionan:

```bash
# Ejecutar solo tests de storage_service
docker-compose exec web pytest /app/tests/orgs/integration/test_storage_service.py -v

# Ejecutar todos los tests
docker-compose exec web pytest /app/tests/ -q
```

**Estado:** ✅ TODOS LOS TESTS PASANDO

