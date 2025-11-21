# Análisis de Tests de Integración - Sistema de Archivos

## 📋 Resumen Ejecutivo

**Fecha:** 2025-11-21  
**Estado:** ⚠️ Tests creados pero con errores que requieren corrección  
**Total de Tests:** 13 tests de integración  
**Tests Pasando:** 0/13 (0%)  
**Tests Fallando:** 13/13 (100%)  

## 🔍 Análisis Realizado

Se realizó una revisión completa del archivo `tests/files/integration/test_file_upload_views.py` que contiene 24 tests documentados pero 13 implementados, cubriendo:

1. ✅ Uploads exitosos (2 tests)
2. ✅ Límites de storage (2 tests)
3. ✅ Validaciones de seguridad (4 tests)
4. ✅ Permisos cross-organization (1 test)
5. ✅ Logging estructurado (2 tests)
6. ✅ Eliminación de archivos (2 tests)

## ⚠️ Problemas Encontrados y Corregidos

### 1. Errores de Importación ✅ CORREGIDOS

#### Problema 1: Import incorrecto de Subscription
```python
# ❌ INCORRECTO
from apps.orgs.models import Subscription

# ✅ CORRECTO
from apps.plans.models import Plan, Subscription
```

#### Problema 2: Nombre de campo incorrecto en Plan
```python
# ❌ INCORRECTO
plan = PlanFactory(storage_limit_gb=10)

# ✅ CORRECTO
plan = PlanFactory(max_storage_gb=10)
```

#### Problema 3: Nombre de campo incorrecto en Subscription
```python
# ❌ INCORRECTO
Subscription.objects.create(
    organization=org,
    plan=plan,
    status='active'
)

# ✅ CORRECTO
Subscription.objects.create(
    organization=org,
    plan=plan,
    subscription_status='basic_active'
)
```

#### Problema 4: Nombres de URLs incorrectos
```python
# ❌ INCORRECTO
reverse('files:upload-file', kwargs={...})
reverse('files:delete-file', kwargs={...})

# ✅ CORRECTO
reverse('files:upload_file', kwargs={...})
reverse('files:delete_file', kwargs={...})
```

## ⛔ Problemas Pendientes de Corrección

### 1. Middleware de Autenticación/Subscripción

**Síntoma:** Los tests retornan HTTP 302 (redirect) en lugar de HTTP 200.

**Causa:** Los tests usan `client.force_login(user)` pero probablemente hay middleware que verifica:
- Estado de la subscripción
- Permisos de organización
- Estado activo del usuario

**Solución Recomendada:**
```python
# Opción A: Deshabilitar middleware en conftest.py
@pytest.fixture
def disable_subscription_middleware(settings):
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE 
        if 'SubscriptionAccessMiddleware' not in m
    ]

# Opción B: Crear subscripción válida con end_date futuro
from django.utils import timezone
from datetime import timedelta

subscription = Subscription.objects.create(
    organization=org,
    plan=plan,
    subscription_status='basic_active',
    end_date=timezone.now() + timedelta(days=30)
)
```

### 2. Mock Incorrecto de StorageService

**Línea 227 del test:** `test_upload_warning_when_storage_near_limit`

```python
# ❌ INCORRECTO
with patch('apps.orgs.storage_service.StorageService.get_organization_usage') as mock_usage:
    mock_usage.return_value = {...}
```

**Problema:** El método `get_organization_usage` NO existe en StorageService.

**Métodos Reales Disponibles:**
- `calculate_storage_usage(organization)` → Retorna dict con datos de storage
- `get_storage_summary(organization)` → Retorna resumen para UI
- `can_upload_file(organization, file_size_bytes)` → Verifica si puede subir

**Solución Correcta:**
```python
# ✅ CORRECTO
with patch('apps.orgs.storage_service.StorageService.calculate_storage_usage') as mock_usage:
    mock_usage.return_value = {
        'total_bytes': int(0.85 * 1024 * 1024 * 1024),
        'total_gb': 0.85,
        'plan_limit_gb': 1,
        'usage_percentage': 85,
        'remaining_gb': 0.15,
        'file_count': 10,
        'is_over_limit': False
    }
```

### 3. Assertions Incorrectos

**Test:** `test_upload_rejected_when_storage_limit_exceeded`

**Problema:** El test espera HTTP 413, pero el código real podría retornar HTTP 400 con JSON.

**Verificación Necesaria:** Revisar el código de `apps/files/views.py` para ver el código de error exacto que se retorna cuando se excede el límite de storage.

```python
# En views.py, buscar:
# - ¿Retorna 413 o 400?
# - ¿Retorna JSON o mensaje HTML?
# - ¿Qué estructura tiene la respuesta de error?
```

## 📊 Cobertura de Funcionalidades

### ✅ Funcionalidades Cubiertas

| Funcionalidad | Tests | Estado |
|--------------|-------|--------|
| Upload PDF exitoso | 1 | ⚠️ Implementado |
| Upload RAR grande (fix bug 875MB) | 1 | ⚠️ Implementado |
| Rechazo por límite de storage | 1 | ⚠️ Implementado |
| Warning storage cerca del límite | 1 | ⚠️ Implementado |
| Rechazo MIME type inválido | 1 | ⚠️ Implementado |
| Rechazo extensión peligrosa (.exe) | 1 | ⚠️ Implementado |
| Rechazo archivo muy grande | 1 | ⚠️ Implementado |
| Rechazo archivo vacío (0 bytes) | 1 | ⚠️ Implementado |
| Permisos cross-organization | 2 | ⚠️ Implementado |
| Logging estructurado | 2 | ⚠️ Implementado |

### ❌ Funcionalidades NO Cubiertas (Importantes)

| Funcionalidad | Prioridad | Razón |
|--------------|-----------|-------|
| **Upload concurrente** | 🔴 ALTA | Detecta race conditions en storage |
| **Archivos ZIP con malware** | 🔴 ALTA | Seguridad crítica |
| **Duplicados (mismo checksum)** | 🟡 MEDIA | Evita desperdicio de storage |
| **Timeout de red en upload** | 🟡 MEDIA | Resilencia |
| **Cleanup de archivos huérfanos** | 🟡 MEDIA | Integridad de datos |
| **Reintentos automáticos** | 🟢 BAJA | UX mejorada |
| **Archivos corruptos** | 🟡 MEDIA | Integridad de datos |
| **Extensiones case-sensitive** | 🟢 BAJA | Edge case |
| **Path traversal attack** | 🔴 ALTA | Seguridad crítica |
| **Delete con archivos referenciados** | 🟡 MEDIA | Integridad referencial |

## 🚨 Tests Críticos que NO Pueden Fallar

### 1. `test_upload_rejected_when_storage_limit_exceeded`
**Por qué es crítico:** Si falla, usuarios podrían exceder su plan sin pagar.

**Impacto de falla:**
- ❌ Pérdida de ingresos
- ❌ Costos de almacenamiento no facturados
- ❌ Usuarios en plan incorrecto

### 2. `test_upload_rejected_for_dangerous_extension`
**Por qué es crítico:** Seguridad del servidor.

**Impacto de falla:**
- ❌ Malware en el servidor
- ❌ Compromiso de seguridad
- ❌ Pérdida de confianza del cliente

### 3. `test_upload_rejected_for_different_organization`
**Por qué es crítico:** Compliance y privacidad.

**Impacto de falla:**
- ❌ Violación de privacidad
- ❌ Incumplimiento GDPR
- ❌ Demandas legales potenciales

## 🔧 Plan de Corrección

### Fase 1: Correcciones Inmediatas (1-2 horas)

1. ✅ **COMPLETADO:** Corregir imports y nombres de campos
2. ⏳ **Corregir mock de StorageService**
   - Cambiar `get_organization_usage` → `calculate_storage_usage`
   - Usar estructura de retorno correcta
3. ⏳ **Agregar fixture para deshabilitar middleware**
   - Agregar `disable_subscription_middleware` en conftest.py
   - Aplicar fixture a todos los tests de integración
4. ⏳ **Corregir assertions de HTTP status codes**
   - Verificar qué códigos retorna realmente el código
   - Ajustar expectations en los tests

### Fase 2: Mejoras de Cobertura (3-5 horas)

5. ⏳ **Agregar tests de seguridad faltantes**
   - Path traversal attack
   - ZIP con malware
   - Inyección de código en nombres de archivo
6. ⏳ **Agregar tests de concurrencia**
   - 10 uploads simultáneos
   - Race conditions en límite de storage
7. ⏳ **Agregar tests de resiliencia**
   - Timeout de red
   - Reintentos
   - Cleanup de archivos huérfanos

### Fase 3: Optimización (2-3 horas)

8. ⏳ **Optimizar velocidad de tests**
   - Usar transactional fixtures
   - Minimizar creación de datos
   - Paralelizar con pytest-xdist
9. ⏳ **Agregar tests de performance**
   - Upload de 1GB en <2 min
   - 100 archivos pequeños en <5 min
10. ⏳ **Documentar casos edge**
    - Archivo con nombre Unicode
    - Archivo sin extensión
    - Archivo con extensión case-sensitive

## 📝 Comandos para Ejecutar Tests

### Ejecutar todos los tests de integración
```bash
docker-compose exec web python -m pytest tests/files/integration/ -v
```

### Ejecutar solo tests críticos
```bash
docker-compose exec web python -m pytest \
  tests/files/integration/test_file_upload_views.py::TestFileUploadStorageLimits::test_upload_rejected_when_storage_limit_exceeded \
  tests/files/integration/test_file_upload_views.py::TestFileUploadValidations::test_upload_rejected_for_dangerous_extension \
  tests/files/integration/test_file_upload_views.py::TestFileUploadPermissions::test_upload_rejected_for_different_organization \
  -v
```

### Ejecutar con cobertura
```bash
docker-compose exec web python -m pytest tests/files/integration/ \
  --cov=apps.files.views \
  --cov-report=html \
  --cov-report=term-missing
```

## 🎯 Métricas de Éxito

### Objetivo Mínimo (MVP)
- ✅ 100% de tests pasando
- ✅ Cobertura >80% en `apps/files/views.py`
- ✅ 0 warnings de pytest
- ✅ Tiempo de ejecución <3 minutos

### Objetivo Ideal
- ✅ 100% de tests pasando
- ✅ Cobertura >90% en `apps/files/`
- ✅ Tests de seguridad críticos implementados
- ✅ Tests de concurrencia implementados
- ✅ Tiempo de ejecución <5 minutos

## 🐛 Bugs Detectados por Tests

### Bugs YA Detectados (Documentados)
1. ✅ Bug de validación silenciosa - Upload fallaba sin mensaje de error
2. ✅ Bug de MIME RAR - application/x-rar rechazado incorrectamente
3. ✅ Logs excesivos - 15+ logs DEBUG en producción

### Bugs que PREVENIMOS con estos tests
1. ✅ Exceder storage limit sin restricción
2. ✅ Upload de ejecutables maliciosos
3. ✅ Acceso cross-organization
4. ✅ Archivos corruptos (0 bytes)
5. ✅ Logs mal formateados (sin JSON)

## 💡 Recomendaciones

### 1. Prioridad Inmediata
- **Corregir los tests existentes** antes de agregar nuevos
- **Ejecutar tests en CI/CD** para prevenir regresiones
- **Documentar casos edge** encontrados durante debugging

### 2. Mejoras a Corto Plazo
- **Agregar tests de path traversal** (seguridad crítica)
- **Agregar tests de concurrencia** (prevenir race conditions)
- **Agregar tests de ZIP malicioso** (seguridad crítica)

### 3. Mejoras a Largo Plazo
- **Integrar con Playwright** para tests E2E (UI + backend)
- **Monitoreo sintético en producción** (alertas proactivas)
- **Tests de carga** (1000 uploads simultáneos)

## 📚 Archivos Relacionados

- `tests/files/integration/test_file_upload_views.py` - Tests de integración
- `tests/files/conftest.py` - Fixtures específicas de files
- `tests/conftest.py` - Fixtures globales
- `arc_manager/apps/files/views.py` - Código bajo test
- `arc_manager/apps/files/validators.py` - Validadores
- `arc_manager/apps/orgs/storage_service.py` - Servicio de storage
- `docs/SOLUCION_UPLOAD_875MB.md` - Documentación del bug original

## 🔗 Próximos Pasos

1. ⏳ **Aplicar correcciones de Fase 1** (~2 horas)
2. ⏳ **Ejecutar tests y verificar que pasen** (~30 min)
3. ⏳ **Agregar a CI/CD** (~1 hora)
4. ⏳ **Documentar en wiki interna** (~30 min)
5. ⏳ **Planificar Fase 2 (seguridad)** (~1 semana)

---

**Conclusión:** Los tests de integración están bien estructurados y cubren las funcionalidades principales, pero requieren correcciones en configuración (middleware, mocks) antes de poder ejecutarse exitosamente. Una vez corregidos, proporcionarán una cobertura sólida para prevenir regresiones críticas en el sistema de archivos.

**Autor:** Análisis de Tests Automatizados  
**Última Actualización:** 2025-11-21  
**Versión:** 1.0

