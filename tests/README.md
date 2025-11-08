# 🧪 ARC Manager - Test Suite Documentation

**Última actualización**: 7 de Noviembre, 2025  
**Framework**: pytest 8.4.2 + pytest-django + Factory Boy  
**Python**: 3.11.13 | Django: 5.2

---

## 📊 Estado General

| Métrica | Valor |
|---------|-------|
| **Tests Totales** | 74 tests (59 unit + 12 integration + 3 security) |
| **Módulos Completos** | ✅ accounts (100%) |
| **Módulos Pendientes** | ⏸️ users, orgs, plans, projects, files, main |
| **Coverage Funcional** | ~70% del módulo accounts |
| **Último Run** | ✅ 100% success rate |
| **Ambiente** | Docker Compose (PostgreSQL) |

⚠️ **IMPORTANTE**: Estructura reorganizada por módulos. Los tests unitarios usan `disable_account_signals` (lógica aislada). Los integration tests prueban comportamiento REAL de producción con signals activos.

---

## 🗂️ Estructura de Tests (REORGANIZADA ✨)

```
tests/
├── conftest.py                          # Fixtures globales y configuración
├── pytest.ini                           # Configuración de pytest
├── README.md                            # 📖 Este archivo (guía principal)
│
├── 📁 docs/                             # Documentación general
│   ├── README.md                        # Índice de documentación
│   ├── CONTINUAR_AQUI.md                # ⭐ Próximos pasos y roadmap
│   └── REORGANIZACION_COMPLETADA.md     # Resumen de cambios
│
├── 🏭 factories/                        # Factory Boy - datos de prueba
│   ├── __init__.py                      # Re-exporta todas las factories
│   ├── accounts/                        # ✅ Factories de accounts
│   │   ├── __init__.py
│   │   └── account_factories.py         # User, SuperUser, OrgAdmin, InactiveUser
│   └── orgs/                            # ✅ Factories de orgs
│       ├── __init__.py
│       └── org_factories.py             # Organization
│
├── 🔐 accounts/                         # ✅ MÓDULO COMPLETO (74 tests)
│   ├── docs/                            # 📚 Documentación específica del módulo
│   │   ├── README.md                    # Índice de docs de accounts
│   │   ├── TESTING_MANUAL.md            # Resumen de pruebas manuales
│   │   ├── MANUAL_TESTING_LOGIN.md      # ⭐ Detalle exhaustivo (2581 líneas)
│   │   └── COBERTURA_TESTS_LOGIN.md     # Análisis de cobertura
│   ├── unit/                            # 59 tests unitarios (signals OFF)
│   │   ├── test_models.py              # 20 tests: modelos base
│   │   ├── test_user_validation.py     # 4 tests: validación RFC
│   │   ├── test_user_unicode.py        # 2 tests: soporte i18n
│   │   ├── test_user_logging.py        # 3 tests: auditoría
│   │   ├── test_user_relationships.py  # 1 test: CASCADE
│   │   ├── test_login_views.py         # 15 tests: autenticación
│   │   ├── test_logout_views.py        # 5 tests: cierre sesión
│   │   ├── test_password_reset_views.py # 7 tests: reset password
│   │   ├── test_force_password_change_views.py # 9 tests: cambio forzado
│   │   ├── test_forms.py               # 13 tests: validación forms
│   │   └── test_middleware.py          # 10 tests: middlewares
│   ├── integration/                     # 12 tests (signals ON)
│   │   └── test_user_signals.py        # Comportamiento producción
│   ├── security/                        # 3 tests críticos
│   │   └── test_user_security.py       # Seguridad crítica
│   └── admin/                           # 🆕 Tests del panel de administración
│       └── test_user_admin.py          # Django Admin: list, forms, permisos
│
├── 👤 users/                            # ⏸️ PENDIENTE
│   └── admin/                           # 🔜 Preparado para tests de admin
│
├── 🏢 orgs/                             # ⏸️ SIGUIENTE (PRIORIDAD ALTA)
│   └── admin/                           # 🔜 Preparado para tests de admin
│       └── test_organization_admin.py  # TODO: OrganizationAdmin, ClientAdmin
│
├── 💳 plans/                            # ⏸️ PENDIENTE (PRIORIDAD ALTA)
│   └── admin/                           # 🔜 Preparado para tests de admin
│       └── test_plan_admin.py          # TODO: PlanAdmin, SubscriptionAdmin, etc
│
├── 📊 projects/                         # ⏸️ PENDIENTE (PRIORIDAD MEDIA)
│   └── admin/                           # 🔜 Preparado para tests de admin
│       └── test_project_admin.py       # TODO: ProjectAdmin, PhaseAdmin, TaskAdmin
│
├── 📁 files/                            # ⏸️ PENDIENTE (PRIORIDAD MEDIA)
│   └── admin/                           # 🔜 Preparado para tests de admin
│       └── test_file_admin.py          # TODO: ProjectFileAdmin, FileSizeFilter
│
└── 🏠 main/                             # ⏸️ PENDIENTE (PRIORIDAD BAJA)
    └── admin/                           # 🔜 Preparado para tests de admin
        └── test_main_admin.py          # TODO: AdminDashboard, SystemSettingsAdmin
```

**Ventajas de esta estructura**:
- ✅ **Modular**: Cada módulo de la app tiene su carpeta de tests
- ✅ **Documentación organizada**: Docs generales vs específicos por módulo
- ✅ **Factories por módulo**: Fácil de encontrar y mantener
- ✅ **Escalable**: Fácil agregar nuevos módulos
- ✅ **Importación flexible**: `from tests.factories import UserFactory`

---

## 🚀 Ejecución de Tests

### ⚠️ IMPORTANTE: Siempre usar Docker

```powershell
# ✅ CORRECTO - Ejecutar en contenedor Docker
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v"

# ❌ INCORRECTO - NO ejecutar localmente
python -m pytest tests/  # Fallará por diferencias de ambiente
```

### Comandos Esenciales

```powershell
# Ejecutar TODOS los tests
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v"

# Ejecutar solo tests del módulo accounts
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/ -v --no-cov"

# Ejecutar por tipo de test
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/unit/ -v"           # Solo unit tests
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/integration/ -v"   # Solo integration
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/security/ -v"      # Solo security
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/admin/ -v"         # Solo admin tests

# Ejecutar tests de admin de otros módulos (cuando estén implementados)
docker-compose exec web bash -c "cd /app && python -m pytest tests/orgs/admin/ -v"
docker-compose exec web bash -c "cd /app && python -m pytest tests/plans/admin/ -v"
docker-compose exec web bash -c "cd /app && python -m pytest tests/projects/admin/ -v"
docker-compose exec web bash -c "cd /app && python -m pytest tests/files/admin/ -v"
docker-compose exec web bash -c "cd /app && python -m pytest tests/main/admin/ -v"

# Ejecutar test específico
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/integration/test_user_signals.py::TestSignalEnsureNamesPresent::test_generates_names_from_email_with_dot -v"

# Ver solo tests fallidos (útil para debugging)
docker-compose exec web bash -c "cd /app && python -m pytest tests/ --lf -v"

# Coverage detallado del módulo accounts
docker-compose exec web bash -c "cd /app && python -m pytest tests/accounts/ --cov=apps.accounts --cov-report=term-missing"

# Ejecutar próximo módulo (cuando esté listo)
docker-compose exec web bash -c "cd /app && python -m pytest tests/orgs/ -v"
```

---

## 📦 Tests Implementados

### 🔵 UNIT TESTS (Lógica Aislada - 59 tests)

Usan fixture `disable_account_signals` para probar lógica en aislamiento.

#### `test_user_models.py` - Tests Base (33 tests)
- CustomUserManager: create_user(), create_superuser()
- Campos: email, username, password, organization, flags
- Métodos: full_name, get_full_name(), __str__()

#### `test_user_logging.py` - Auditoría (3 tests)
- Structured logging para compliance (GDPR, SOX, ISO 27001)
- Events: user_created, superuser_created, user_creation_failed

#### `test_user_unicode.py` - Internacionalización (2 tests)
- Soporte UTF-8 para 10 idiomas
- 20 test cases (español, francés, alemán, ruso, chino, japonés, árabe, hindi, coreano, hebreo)

#### `test_user_validation.py` - Validaciones RFC (4 tests)
- Email max 254 chars (RFC 5321)
- first_name/last_name max 50 chars
- Email normalization (case-insensitive)

#### `test_user_relationships.py` - Relaciones (1 test)
- ForeignKey CASCADE delete Organization

---

### 🟢 INTEGRATION TESTS (Comportamiento Real - 12 tests)

**NO usan** `disable_account_signals` → Signals ACTIVOS como en producción.

#### `test_user_signals.py` - Signals en Producción (12 tests)

**🔑 DIFERENCIA CRÍTICA:**
- ❌ **Unit tests**: `disable_account_signals` → NO reflejan producción
- ✅ **Integration tests**: Signals ACTIVOS → Comportamiento REAL

**📋 FLUJO DE PRODUCCIÓN CORRECTO:**
1. Admin crea `Organization` (sin subscription)
2. Admin asigna `Plan` ('trial' o 'basic')
3. Sistema crea `Subscription`
4. Recién ahí se pueden crear usuarios

**Tests por Signal:**

1. **`ensure_names_present` (4 tests)**
   - ✅ Auto-genera nombres desde email con punto: `john.doe@x.com` → `John` + `Doe`
   - ✅ Auto-genera nombres desde email sin punto: `admin@x.com` → `Admin` + `Usuario`
   - ✅ Respeta nombres provistos por usuario
   - ✅ Maneja emails con múltiples puntos: `john.paul.jones@x.com` → `John` + `Paul`

2. **`validate_admin_without_org` (3 tests)**
   - ✅ Rechaza admins de org sin organización (ValidationError)
   - ✅ Permite admins CON organización
   - ✅ Permite usuarios regulares inactivos sin org

3. **`validate_user_organization` (3 tests)**
   - ✅ Rechaza usuarios activos sin organización (ValidationError)
   - ✅ Permite superusers sin organización
   - ✅ Permite usuarios inactivos sin organización

4. **`validate_organization_limits` (3 tests)**
   - ✅ Permite crear usuarios dentro del límite del plan
   - ✅ Rechaza usuarios que exceden límite (ValidationError)
   - ✅ Superusers no cuentan para límite (no tienen org asignada)

5. **Integration Flow (1 test)**
   - ✅ Flujo end-to-end con TODOS los signals activos simultáneamente

---

### 🔴 SECURITY TESTS (3 tests)

#### `test_user_security.py` - Seguridad
- ✅ Email case-insensitive unique (previene duplicados)
- ✅ Passwords never logged (CRÍTICO - compliance)
- ✅ Timing attack resistance (check_password constante)

---

## 🎯 Coverage por Categoría

| Categoría | Tests | Estado | Signals |
|-----------|-------|--------|---------|
| **Unit Tests** | 59 | ✅ | Desactivados |
| **Integration Tests** | 12 | ✅ | Activos |
| **Security Tests** | 3 | ✅ | Desactivados |
| **Total** | **74** | ✅ | Mixto |

**Coverage Real**: ~70% del módulo accounts completo

---

## 📚 Documentación

### 📁 Documentación General (`docs/`)
👉 **[docs/CONTINUAR_AQUI.md](docs/CONTINUAR_AQUI.md)** - Estado actual + próximos pasos + roadmap  
📝 **[docs/REORGANIZACION_COMPLETADA.md](docs/REORGANIZACION_COMPLETADA.md)** - Resumen de cambios

### 📁 Documentación del Módulo Accounts (`accounts/docs/`)
📋 **[accounts/docs/TESTING_MANUAL.md](accounts/docs/TESTING_MANUAL.md)** - Resumen ejecutivo de pruebas  
⭐ **[accounts/docs/MANUAL_TESTING_LOGIN.md](accounts/docs/MANUAL_TESTING_LOGIN.md)** - Guía exhaustiva (2581 líneas)  
📊 **[accounts/docs/COBERTURA_TESTS_LOGIN.md](accounts/docs/COBERTURA_TESTS_LOGIN.md)** - Análisis de cobertura

### 🏭 Factories (`factories/`)
```python
# Importación fácil desde cualquier lugar
from tests.factories import UserFactory, OrganizationFactory

# O importar desde el módulo específico
from tests.factories.accounts import UserFactory
from tests.factories.orgs import OrganizationFactory
```

---

## 🔧 Configuración

### pytest.ini
```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
```

### Fixtures Disponibles (conftest.py)
- `disable_account_signals`: Desactiva signals para unit tests
- `user_factory`: Factory de usuarios
- `organization_factory`: Factory de organizaciones

---

## 🐛 Bugs Encontrados y Resueltos

### 🔴 CRÍTICO - Email Case-Sensitive (RESUELTO)
**Problema**: `TEST@X.COM` y `test@x.com` permitían duplicados  
**Solución**: Añadido `.lower()` en `CustomUserManager.create_user()`  
**Test**: `test_email_case_insensitive_unique`

---

## 📈 Progreso por Módulo

| Módulo | Tests | Admin Tests | Estado | Prioridad | Tiempo Estimado |
|--------|-------|-------------|--------|-----------|-----------------|
| **accounts** | 74 | ✅ Estructura lista | ✅ Completo | - | - |
| **users** | 0 | 🔜 Estructura lista | ⏸️ Pendiente | Baja | 1 día |
| **orgs** | 0 | 🔜 Estructura lista | ⏸️ Siguiente | 🔴 CRÍTICA | 5-7 días |
| **plans** | 0 | 🔜 Estructura lista | ⏸️ Pendiente | 🔴 CRÍTICA | 4-6 días |
| **projects** | 0 | 🔜 Estructura lista | ⏸️ Pendiente | 🟠 Alta | 4-5 días |
| **files** | 0 | 🔜 Estructura lista | ⏸️ Pendiente | 🟠 Alta | 3-4 días |
| **main** | 0 | 🔜 Estructura lista | ⏸️ Pendiente | 🟢 Baja | 1-2 días |
| **TOTAL** | **74/~330** | **6 módulos prep.** | **22%** | - | **18-25 días** |

### 🆕 Tests de Admin Panel (Django Admin)

Todos los módulos ahora tienen la estructura preparada para probar el panel de administración Django:

- **accounts/admin/** → `test_user_admin.py` ✅ Completo
- **orgs/admin/** → `test_organization_admin.py` 🔜 Preparado (OrganizationAdmin, ClientAdmin)
- **plans/admin/** → `test_plan_admin.py` 🔜 Preparado (PlanAdmin, SubscriptionAdmin, UpgradeRequestAdmin, PaymentAdmin, RenewalRequestAdmin)
- **projects/admin/** → `test_project_admin.py` 🔜 Preparado (ProjectAdmin, PhaseAdmin, TaskAdmin, PhaseTemplateAdmin)
- **files/admin/** → `test_file_admin.py` 🔜 Preparado (ProjectFileAdmin, FileSizeFilter)
- **main/admin/** → `test_main_admin.py` 🔜 Preparado (AdminDashboard, SystemSettingsAdmin)

Cada archivo incluye:
- ✅ Estructura base con fixtures (admin_site, admin_user, admin_request)
- ✅ Clases de test organizadas por funcionalidad
- ✅ TODOs detallados con qué probar
- ✅ Referencias al archivo admin.py correspondiente

---

## 💡 Convenciones de Testing

### Naming
```python
test_<funcionalidad>_<aspecto>_<condicion>
```

### Docstrings
```python
"""
Test <funcionalidad>.

Why?
----
<Razón de negocio/técnica>

What?
-----
<Qué valida exactamente>

What if fails?
--------------
<Impacto si falla>
"""
```

### Markers
```python
@pytest.mark.unit       # Lógica aislada
@pytest.mark.integration  # Signals activos
@pytest.mark.security   # Vulnerabilidades
```

---

**Happy Testing! 🧪**
