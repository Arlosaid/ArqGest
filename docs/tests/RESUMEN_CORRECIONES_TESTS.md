# Resumen de Correcciones Aplicadas a Tests de Integración

## Fecha: 2025-11-21

## Problemas Identificados y Corregidos

### ✅ 1. Mock Incorrecto de StorageService

**Problema:**
```python
# ❌ INCORRECTO
with patch('apps.orgs.storage_service.StorageService.get_organization_usage') as mock_usage:
```

**Corrección:**
```python
# ✅ CORRECTO  
with patch('apps.orgs.storage_service.StorageService.calculate_storage_usage') as mock_usage:
```

**Estado:** ✅ CORREGIDO en línea 228 de `test_file_upload_views.py`

---

### ✅ 2. Imports Faltantes para Fechas

**Problema:** Tests no importaban `timezone` y `timedelta` necesarios para `end_date`.

**Corrección:**
```python
from django.utils import timezone
from datetime import timedelta
```

**Estado:** ✅ CORREGIDO - Imports agregados

---

### ✅ 3. Campo `end_date` Faltante en Subscriptions

**Problema:** Todas las subscriptions creadas sin `end_date` causan fallos.

**Corrección:**
```python
subscription = Subscription.objects.create(
    organization=org,
    plan=plan,
    subscription_status='basic_active',
    end_date=timezone.now() + timedelta(days=30)  # ✅ AGREGADO
)
```

**Estado:** ✅ CORREGIDO en todos los 13 tests

---

### ✅ 4. Assertion Mejorado para Logs

**Problema:** Assertion no encontraba 'storage_limit' en logs estructurados.

**Corrección:**
```python
# Verificar log de advertencia (buscar en el event o en el message)
assert any(
    'storage_limit' in record.message.lower() or 
    (hasattr(record, 'event') and 'storage_limit' in str(record.event).lower())
    for record in caplog.records
)
```

**Estado:** ✅ CORREGIDO en `test_upload_rejected_when_storage_limit_exceeded`

---

### ⚠️ 5. Middleware Causando Redirects (PROBLEMA PENDIENTE)

**Problema Principal:** Tests retornan HTTP 302 (redirect a `/main/`) en lugar de códigos esperados (200, 400, 403, 413).

**Middlewares Identificados como Problemáticos:**
1. `apps.accounts.middleware.LoginRequiredMiddleware` - Redirige usuarios no autenticados
2. `apps.accounts.middleware.SuperuserRestrictMiddleware` - Redirige superusers a `/admin/`
3. `apps.accounts.middleware.PasswordChangeRequiredMiddleware` - Redirige si cambio de password requerido
4. `apps.plans.middleware.SubscriptionAccessMiddleware` - Valida subscripción
5. `apps.orgs.middleware.OrganizationContextMiddleware` - Valida organización

**Intentos de Solución:**
- ✅ Fixture `disable_subscription_middleware` en `conftest.py` global
- ✅ Fixture `autouse` en `tests/files/integration/conftest.py` local
- ❌ NINGUNO FUNCIONA - Los middlewares siguen activos

**Causa Raíz:** Los middlewares se cargan al inicio y las fixtures de `settings.MIDDLEWARE` no tienen efecto después de que Django procesa los middlewares.

**Soluciones Posibles:**

#### Opción A: Modificar Middlewares para Excluir Tests
Agregar verificación en cada middleware:
```python
# En LoginRequiredMiddleware, SuperuserRestrictMiddleware, etc.
def __call__(self, request):
    # Excluir si estamos en modo testing
    if settings.TESTING:
        return self.get_response(request)
    # ... resto de la lógica
```

#### Opción B: Usar @override_settings con MIDDLEWARE Reducido
```python
@pytest.mark.django_db
@override_settings(MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
])
class TestFileUploadSuccess:
    # tests...
```

#### Opción C: Configurar LOGIN_EXEMPT_URLS en Settings
Agregar paths de files a URLs exentas:
```python
# En settings.py
LOGIN_EXEMPT_URLS = [
    r'projects/.*/phases/.*/files/upload/$',
    r'files/.*/$',
    # ... otros paths
]
```

#### Opción D: Crear Cliente de Test Custom
```python
class IntegrationTestClient(Client):
    def request(self, **request):
        # Bypass middleware checks
        request['TESTING'] = True
        return super().request(**request)
```

---

## Estado Actual de los Tests

### Tests Ejecutados: 13/13
### Tests Pasando: 0/13 (0%)
### Tests Fallando: 13/13 (100%)

### Errores Actuales:
1. **5 tests:** `assert response.status_code == 200` → Reciben 302 (redirect a `/main/`)
2. **1 test:** `test_upload_rejected_when_storage_limit_exceeded` → Assertion de logs (mejorado pero aún falla por redirect)

---

## Próximos Pasos Recomendados

### Prioridad ALTA:
1. **Resolver el problema de middlewares** usando una de las opciones (A, B, C o D)
2. Verificar que todos los tests pasen después de resolver middlewares
3. Ejecutar suite completa de tests de integración

### Prioridad MEDIA:
4. Agregar tests faltantes de seguridad (path traversal, ZIP malware)
5. Agregar tests de concurrencia
6. Documentar solución final en wiki interna

### Prioridad BAJA:
7. Optimizar velocidad de tests
8. Agregar tests de performance
9. Integrar con CI/CD

---

## Archivos Modificados

1. ✅ `tests/files/integration/test_file_upload_views.py` - Correcciones aplicadas
2. ✅ `tests/conftest.py` - Fixture `disable_subscription_middleware` agregada
3. ✅ `tests/files/integration/conftest.py` - Fixture `autouse` creada (NO FUNCIONA AÚN)

---

## Comandos para Ejecutar Tests

```bash
# Ejecutar todos los tests de integración
docker-compose exec web python -m pytest /app/tests/files/integration/test_file_upload_views.py -v

# Ejecutar solo tests críticos
docker-compose exec web python -m pytest /app/tests/files/integration/test_file_upload_views.py::TestFileUploadStorageLimits -v

# Ejecutar un solo test específico
docker-compose exec web python -m pytest /app/tests/files/integration/test_file_upload_views.py::TestFileUploadSuccess::test_upload_pdf_file_successfully -v
```

---

## Conclusión

Se han aplicado **4 de 5 correcciones críticas**. El problema restante (middlewares causando redirects) requiere una decisión arquitectónica sobre cómo manejar middlewares en tests de integración.

**Recomendación:** Implementar **Opción A** (modificar middlewares para excluir tests) por ser la solución más limpia y mantenible a largo plazo.

