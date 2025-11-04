# Plan Completo de Testing para ARC Manager

**Proyecto**: ARC Manager (Django Application)  
**Fecha de Creación**: 4 de Noviembre, 2025  
**Última Actualización**: 4 de Noviembre, 2025 - Sesión 3 (Documentación Completa)  
**Branch**: feat-unitest-login  
**Objetivo**: Implementar una suite ROBUSTA, COMPLETA y TRAZABLE de tests (Happy Path + Edge Cases + Logging + Security)

---

## 📋 TABLA DE CONTENIDOS

1. [Filosofía de Testing](#-filosofía-de-testing)
2. [Estrategia de Logging y Trazabilidad](#-estrategia-de-logging-y-trazabilidad)
3. [Estado Actual del Proyecto](#-estado-actual-del-proyecto)
4. [Stack de Testing](#️-stack-de-testing)
5. [Estructura de Archivos](#-estructura-de-archivos)
6. [Configuración Inicial](#️-configuración-inicial)
7. [Análisis Detallado de Tests Implementados](#-análisis-detallado-de-tests-implementados)
8. [Tests Faltantes (Críticos)](#-tests-faltantes-críticos)
9. [Matriz de Cobertura](#-matriz-de-cobertura)
10. [Plan de Implementación por Fases](#-plan-de-implementación-por-fases)
11. [Guía Detallada por Módulo](#-guía-detallada-por-módulo)
12. [Patrones y Mejores Prácticas](#-patrones-y-mejores-prácticas)
13. [Comandos Útiles](#-comandos-útiles)
14. [Métricas y Objetivos](#-métricas-y-objetivos)
15. [Checklist de Progreso](#-checklist-de-progreso)
16. [Glosario y Conceptos Clave](#-glosario-y-conceptos-clave)

---

## 🧠 FILOSOFÍA DE TESTING

### Pirámide de Testing (Estrategia 70-20-10)

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E ╲         10% - End to End Tests
                 ╱  (5)  ╲        • Tests completos de flujos críticos
                ╱─────────╲       • Lentos pero realistas
               ╱           ╲
              ╱ Integration ╲     20% - Integration Tests  
             ╱     (50)      ╲    • Tests de múltiples componentes
            ╱─────────────────╲   • Incluyen signals, BD, cache
           ╱                   ╲
          ╱   Unit Tests (250)  ╲ 70% - Unit Tests
         ╱                       ╲ • Tests aislados y rápidos
        ╱_________________________╲ • Mock de dependencias externas
```

### Tres Capas de Testing

#### **CAPA 1: Unit Tests (Sin Signals, Sin Dependencias Externas)**

**Objetivo**: Probar la lógica pura del código de forma aislada.

**Características:**
- ✅ **Rápidos**: <1 segundo por test
- ✅ **Aislados**: Sin efectos secundarios
- ✅ **Predecibles**: Mismo input = mismo output
- ⚠️ **Deshabilitan signals**: No prueban comportamiento real completo

**Cuándo usar:**
```python
# ✅ USAR para lógica de negocio pura
def test_full_name_property(self, disable_account_signals):
    """Probar SOLO el cálculo de full_name sin signals"""
    user = UserFactory(first_name='John', last_name='Doe')
    assert user.full_name == 'John Doe'

# ✅ USAR para validaciones de modelo
def test_email_must_be_unique(self, disable_account_signals):
    """Probar constraint de BD sin signals"""
    User.objects.create_user(email='test@example.com', ...)
    with pytest.raises(IntegrityError):
        User.objects.create_user(email='test@example.com', ...)
```

**Logs esperados**: Ninguno (o logs de DEBUG si acaso)

---

#### **CAPA 2: Integration Tests (Con Signals, Con BD, Con Cache)**

**Objetivo**: Probar flujos completos que involucran múltiples componentes.

**Características:**
- ⏱️ **Moderados**: 1-5 segundos por test
- 🔗 **Realistas**: Comportamiento en producción
- 📊 **Incluyen signals**: Prueban todo el flujo
- ⚠️ **Pueden fallar por múltiples razones**: Más difícil debuggear

**Cuándo usar:**
```python
# ✅ USAR para flujos de creación completos
@pytest.mark.integration
def test_user_creation_triggers_signals(self):
    """Probar que signals se ejecutan correctamente"""
    # NO usar disable_account_signals
    user = User.objects.create_user(
        email='john.doe@example.com',
        password='pass',
        first_name='',  # Signal lo llenará
        last_name=''
    )
    
    # Signal ensure_names_present debe haber actuado
    assert user.first_name == 'John'
    assert user.last_name == 'Doe'

# ✅ USAR para validaciones de negocio
@pytest.mark.integration
def test_admin_without_org_is_rejected(self):
    """Probar que signal rechaza admin sin organización"""
    with pytest.raises(ValidationError, match='administradores.*organización'):
        User.objects.create_user(
            email='admin@example.com',
            password='pass',
            first_name='Admin',
            last_name='User',
            is_org_admin=True,
            organization=None  # Signal debe rechazar esto
        )
```

**Logs esperados:**
- ✅ INFO: Creación exitosa
- ⚠️ WARNING: Validaciones que fallan
- ❌ ERROR: Errores inesperados

---

#### **CAPA 3: E2E Tests (Sistema Completo: API → Services → BD)**

**Objetivo**: Probar flujos críticos desde la perspectiva del usuario final.

**Características:**
- 🐌 **Lentos**: 5-30 segundos por test
- 🎯 **Realistas**: Exactamente como en producción
- 🌐 **Incluyen API**: Tests de endpoints HTTP
- ⚠️ **Frágiles**: Pueden fallar por cualquier cosa

**Cuándo usar:**
```python
# ✅ USAR para flujos críticos de negocio
@pytest.mark.e2e
def test_user_registration_complete_flow(self, api_client):
    """Probar registro completo desde API hasta BD"""
    response = api_client.post('/api/auth/register/', {
        'email': 'newuser@example.com',
        'password': 'SecurePass123!',
        'first_name': 'New',
        'last_name': 'User'
    })
    
    assert response.status_code == 201
    
    # Verificar que se creó en BD
    user = User.objects.get(email='newuser@example.com')
    assert user.first_name == 'New'
    
    # Verificar que signal actuó
    assert user.username is not None
```

**Logs esperados:**
- ✅ INFO: Cada paso del flujo
- 📊 BUSINESS_EVENT: Eventos de negocio importantes
- ⚠️ WARNING: Problemas recuperables
- ❌ ERROR: Fallos críticos

---

## 📊 ESTRATEGIA DE LOGGING Y TRAZABILIDAD

### Niveles de Logging por Tipo de Operación

```python
# 🎯 BUSINESS EVENTS (INFO) - Auditoría y métricas de negocio
log_business_event(
    event="user_created",
    action="created",
    entity_type="user",
    entity_id=user.id,
    user_email=user.email,
    organization_id=org.id if org else None
)
# Cuándo: Creación exitosa de entidades importantes
# Por qué: Auditoría, cumplimiento legal, métricas de negocio

# ℹ️ INFO - Operaciones exitosas normales
log_info(
    event="password_changed",
    message="Usuario cambió su contraseña",
    user_id=user.id,
    user_email=user.email
)
# Cuándo: Operaciones exitosas que no son eventos de negocio
# Por qué: Trazabilidad de operaciones

# ⚠️ WARNING - Problemas recuperables o comportamientos sospechosos
log_warning(
    event="login_failed",
    message="Intento de login con contraseña incorrecta",
    user_email=email,
    ip_address=request.META.get('REMOTE_ADDR'),
    attempt_count=failed_attempts
)
# Cuándo: Validaciones que fallan, intentos fallidos, límites alcanzados
# Por qué: Detectar ataques, monitorear comportamientos anormales

# ❌ ERROR - Errores inesperados que requieren investigación
log_error(
    event="database_connection_failed",
    error_code="DB001",
    error_message=str(e),
    user_id=user.id if user else None
)
# Cuándo: Excepciones, fallos de sistema, errores de BD
# Por qué: Debugging, alertas, resolución de incidentes
```

### Campos Obligatorios en Logs Estructurados

```python
# SIEMPRE incluir:
{
    "event": str,          # Nombre del evento (snake_case)
    "timestamp": datetime, # Auto-agregado por logger
    "level": str,         # Auto-agregado (INFO, WARNING, ERROR)
    
    # Si está disponible:
    "user_id": int,       # ID del usuario que ejecuta la acción
    "organization_id": int, # ID de la organización
    "request_id": str,    # UUID del request (para rastreo)
    "ip_address": str,    # IP del cliente
    
    # Para errores:
    "error_code": str,    # Código de error (USR001, ORG002, etc.)
    "error_message": str, # Mensaje de error
    "stack_trace": str,   # Solo en DEBUG
    
    # Para eventos de negocio:
    "action": str,        # created, updated, deleted
    "entity_type": str,   # user, project, transaction
    "entity_id": int,     # ID de la entidad
    "outcome": str        # success, failure
}
```

### Matriz de Logging por Operación

| Operación | Nivel | Event Name | Cuándo Loggear | Por Qué |
|-----------|-------|------------|----------------|---------|
| Crear usuario exitosamente | INFO | `user_created` | Después de save() | Auditoría legal |
| Crear usuario (fallo) | ERROR | `user_creation_failed` | Catch exception | Debugging |
| Login exitoso | INFO | `user_logged_in` | Después de authenticate() | Seguridad |
| Login fallido | WARNING | `login_failed` | Contraseña incorrecta | Detectar ataques |
| 5+ intentos fallidos | ERROR | `brute_force_detected` | Umbral alcanzado | Seguridad crítica |
| Cambio de contraseña | INFO | `password_changed` | Después de set_password() | Auditoría |
| Eliminar usuario | WARNING | `user_deleted` | Antes de delete() | Auditoría crítica |
| Actualizar email | INFO | `email_updated` | Después de save() | Trazabilidad |
| Alcanzar límite de usuarios | WARNING | `org_user_limit_reached` | Pre-save signal | Upsell opportunity |
| Error de BD | ERROR | `database_error` | Catch exception | Alertas críticas |

---

---

## 🎯 ESTADO ACTUAL DEL PROYECTO

### ✅ Completado (Sesiones 1-2 - 4 Nov 2025)

#### **Sesión 1 - Setup Inicial**
**Configuración Base:**
- ✅ `pytest.ini` creado y configurado en raíz del proyecto
- ✅ `.coveragerc` creado y configurado  
- ✅ `tests/conftest.py` con fixtures globales funcionales
- ✅ Dependencias de testing instaladas en Docker
- ✅ `docker-compose.yml` actualizado con volúmenes de tests
- ✅ `requirements.txt` actualizado con dependencias de testing

**Factories Creadas:**
- ✅ `tests/factories/account_factories.py` - 4 factories
  - UserFactory (usuario básico con organización)
  - SuperUserFactory (superusuario con permisos completos)
  - OrgAdminFactory (administrador de organización)
  - InactiveUserFactory (usuario inactivo)
- ✅ `tests/factories/org_factories.py` - OrganizationFactory

#### **Sesión 2 - Tests del Modelo User**
**Tests Implementados:**
- ✅ `tests/unit/test_accounts/test_models.py` - **33 tests (100% PASSING)** ✅
  - ✅ TestUserCreation (5 tests) - Creación básica de usuarios
  - ✅ TestUserValidation (4 tests) - Validaciones de email y username
  - ✅ TestUserPassword (5 tests) - Hashing y validación de contraseñas
  - ✅ TestUserMethods (11 tests) - Métodos del modelo
  - ✅ TestUserSpecialFields (3 tests) - Campos especiales
  - ✅ TestUserDatabase (5 tests) - Operaciones de BD

**Bugs Críticos Encontrados y Arreglados:**
1. ✅ **Bug en `structured_logging.py`**:
   - Problema: `data['message']` conflictuaba con LogRecord.message
   - Solución: Cambiado a `data['detail']`
   - Impacto: Hubiera causado errores en producción
   
2. ✅ **Signal `ensure_names_present`** auto-llenaba nombres:
   - Problema: Tests esperaban nombres vacíos pero signal los llenaba
   - Solución: Agregado al fixture `disable_account_signals`

**Infraestructura:**
- ✅ Fixture `disable_account_signals` con 4 signals desconectados:
  - `validate_user_organization`
  - `validate_organization_limits`
  - `ensure_names_present`
  - `validate_admin_without_org`

### 📊 Progreso General

| Fase | Componente | Tests | Estado | Cobertura Real |
|------|-----------|-------|--------|----------------|
| 1 | Setup & Config | - | ✅ 100% | - |
| 1 | Factories (accounts) | - | ✅ 100% | - |
| 1 | Factories (orgs) | - | ✅ 100% | - |
| 1 | User Model (Unit) | 33/33 | ✅ 100% | 🟡 48% (falta edge cases) |
| 1 | User Model (Integration) | 0/10 | ❌ 0% | ❌ 0% |
| 1 | User Model (E2E) | 0/5 | ❌ 0% | ❌ 0% |
| 2 | Factories (plans) | - | ❌ 0% | - |
| 2 | Factories (projects) | - | ❌ 0% | - |
| 2 | Organization Model | 0/25 | ❌ 0% | ❌ 0% |
| 2 | Plan Model | 0/20 | ❌ 0% | ❌ 0% |

**Métricas Actuales:**
- ✅ Tests pasando: **33/33 (100%)**
- ⚠️ Cobertura nominal: **48%** (solo happy path básico)
- ❌ Edge cases cubiertos: **0%**
- ❌ Integration tests: **0%**
- ❌ Security tests: **0%**
- ❌ Logging tests: **0%**

---

## 🛠️ STACK DE TESTING

### Dependencias Principales

```txt
# Testing Framework
pytest==7.4.3                # Framework principal de testing
pytest-django==4.7.0         # Integración con Django
pytest-cov==4.1.0            # Coverage reporting
pytest-xdist==3.5.0          # Ejecución paralela de tests
pytest-mock==3.12.0          # Mocking avanzado

# Generación de Datos
factory-boy==3.3.0           # Factories para crear objetos de prueba
faker==20.1.0                # Datos aleatorios realistas

# Utilities
freezegun==1.4.0             # Mock de fechas/tiempo
responses==0.24.1            # Mock de requests HTTP
```

### ¿Por qué estos tools?

| Tool | Propósito | Alternativa | ¿Por qué elegimos esto? |
|------|-----------|-------------|-------------------------|
| pytest | Framework | unittest | Más pythonic, fixtures poderosos, mejor output |
| factory-boy | Datos de prueba | Fixtures JSON | Más flexible, menos mantenimiento |
| faker | Datos aleatorios | Datos hardcodeados | Encuentra edge cases que no pensaste |
| pytest-cov | Coverage | coverage.py | Integración directa con pytest |
| freezegun | Time mocking | Mock manual | API simple para tests de tiempo |

---

## 📂 ESTRUCTURA DE ARCHIVOS

### Estructura Completa del Directorio `tests/`

```
tests/
├── __init__.py
├── conftest.py                          # ⚙️ Configuración global y fixtures
├── pytest.ini                           # ⚙️ Config pytest (en raíz proyecto)
├── .coveragerc                          # ⚙️ Config coverage (en raíz proyecto)
├── PLAN_TESTING_COMPLETO.md            # 📚 Este documento
├── TESTS_DOCUMENTATION.md              # 📚 Documentación detallada de tests
│
├── factories/                           # 🏭 Factory Boy factories
│   ├── __init__.py
│   ├── account_factories.py             # ✅ User, SuperUser, OrgAdmin, InactiveUser
│   ├── org_factories.py                 # ✅ Organization, OrganizationMember
│   ├── project_factories.py             # ❌ TODO: Project, ProjectMember, Transaction
│   ├── plan_factories.py                # ❌ TODO: Plan, Subscription
│   └── file_factories.py                # ❌ TODO: FileUpload
│
├── fixtures/                            # 📁 Datos estáticos
│   ├── sample_files/
│   │   ├── test_image.jpg
│   │   ├── test_document.pdf
│   │   └── test_malware.exe
│   └── test_data.json
│
├── unit/                                # 🧪 Tests unitarios (70%)
│   ├── __init__.py
│   │
│   ├── test_accounts/
│   │   ├── __init__.py
│   │   ├── test_models.py               # ✅ 33/33 tests (User model)
│   │   ├── test_edge_cases.py           # ❌ TODO: 25 edge cases críticos
│   │   ├── test_security.py             # ❌ TODO: SQL injection, XSS, timing attacks
│   │   ├── test_views.py                # ❌ TODO: Login, register, profile
│   │   ├── test_forms.py                # ❌ TODO: Form validation
│   │   └── test_middleware.py           # ❌ TODO: Auth middleware
│   │
│   ├── test_orgs/
│   │   ├── test_models.py               # ❌ TODO: Organization, Member
│   │   ├── test_storage_service.py      # ❌ TODO: R2/S3 operations
│   │   ├── test_cache_utils.py          # ❌ TODO: Cache invalidation
│   │   └── test_decorators.py           # ❌ TODO: @require_org_member
│   │
│   ├── test_plans/
│   │   ├── test_models.py               # ❌ TODO: Plan, Subscription
│   │   ├── test_services.py             # ❌ TODO: Subscription logic
│   │   └── test_middleware.py           # ❌ TODO: Plan enforcement
│   │
│   ├── test_projects/
│   │   ├── test_models.py               # ❌ TODO: Project, Transaction
│   │   ├── test_finance_cache.py        # ❌ TODO: Financial calculations
│   │   └── test_managers.py             # ❌ TODO: Custom QuerySets
│   │
│   ├── test_files/
│   │   ├── test_models.py               # ❌ TODO: FileUpload model
│   │   ├── test_security.py             # ❌ TODO: Malware scan, validation
│   │   ├── test_api.py                  # ❌ TODO: Upload/download endpoints
│   │   └── test_validators.py           # ❌ TODO: File type/size validators
│   │
│   └── test_core/
│       ├── test_email_utils.py          # ❌ TODO: Email sending
│       ├── test_validators.py           # ❌ TODO: Custom validators
│       └── test_health.py               # ❌ TODO: Health check endpoint
│
├── integration/                         # 🔗 Tests de integración (20%)
│   ├── __init__.py
│   ├── test_user_signals.py             # ❌ TODO: Signals con BD y cache
│   ├── test_user_onboarding.py          # ❌ TODO: Registro → Org → Plan
│   ├── test_subscription_workflow.py    # ❌ TODO: Plan → Payment → Activation
│   ├── test_project_lifecycle.py        # ❌ TODO: Create → Transactions → Close
│   ├── test_file_upload_workflow.py     # ❌ TODO: Upload → Validate → Store
│   └── test_logging.py                  # ❌ TODO: Verificar logs correctos
│
├── e2e/                                 # 🌐 Tests end-to-end (10%)
│   ├── __init__.py
│   ├── test_user_registration_api.py    # ❌ TODO: API de registro completa
│   ├── test_login_flow.py               # ❌ TODO: Login desde API
│   └── test_critical_paths.py          # ❌ TODO: Flujos críticos de negocio
│
└── performance/                         # ⚡ Tests de rendimiento (opcional)
    ├── __init__.py
    └── test_query_performance.py        # ❌ TODO: N+1 queries, bulk operations
```

**Leyenda:**
- ✅ = Implementado y funcionando
- ❌ TODO = Pendiente de implementar
- 🧪 = Unit test
- 🔗 = Integration test
- 🌐 = E2E test
- ⚡ = Performance test

---

## ⚙️ CONFIGURACIÓN INICIAL

### 1. Archivo `pytest.ini` (Raíz del proyecto)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=arc_manager
    --cov-report=html
    --cov-report=term-missing:skip-covered
    --cov-fail-under=80
    --maxfail=5
    --reuse-db
    
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests (with signals, BD, cache)
    unit: marks tests as unit tests (isolated, no signals)
    smoke: marks tests as smoke tests (critical paths)
    security: marks tests as security-focused
    wip: marks tests as work in progress
    
testpaths = tests
```

### 2. Archivo `.coveragerc` (Raíz del proyecto)

```ini
[run]
source = arc_manager
omit = 
    */migrations/*
    */tests/*
    */test_*.py
    */__pycache__/*
    */settings.py
    */wsgi.py
    */asgi.py
    manage.py
    */venv/*
    */virtualenv/*

[report]
precision = 2
show_missing = True
skip_covered = False

exclude_lines =
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if settings.DEBUG:
    if TYPE_CHECKING:
    @abstract
    @abc.abstractmethod

[html]
directory = htmlcov
```

### 3. Fixtures Disponibles en `tests/conftest.py`

```python
# 🌐 Clientes HTTP
@pytest.fixture
def api_client():
    """Cliente Django básico para requests"""
    return Client()

@pytest.fixture
def authenticated_client(db, user):
    """Cliente autenticado con usuario regular"""
    client = Client()
    client.force_login(user)
    return client

@pytest.fixture
def admin_client(db, superuser):
    """Cliente autenticado con superusuario"""
    client = Client()
    client.force_login(superuser)
    return client

# 👤 Usuarios
@pytest.fixture
def user(db):
    """Usuario básico con organización"""
    from tests.factories.account_factories import UserFactory
    return UserFactory()

@pytest.fixture
def superuser(db):
    """Superusuario con permisos completos"""
    from tests.factories.account_factories import SuperUserFactory
    return SuperUserFactory()

# ⚙️ Configuración de Tests
@pytest.fixture
def disable_account_signals():
    """Deshabilita signals de validación para unit tests"""
    from django.db.models import signals
    from apps.accounts import signals as account_signals
    from apps.accounts.models import User
    
    # Desconectar 4 signals
    signals.pre_save.disconnect(account_signals.validate_user_organization, sender=User)
    signals.pre_save.disconnect(account_signals.validate_organization_limits, sender=User)
    signals.pre_save.disconnect(account_signals.ensure_names_present, sender=User)
    signals.pre_save.disconnect(account_signals.validate_admin_without_org, sender=User)
    
    yield  # Tests se ejecutan aquí
    
    # Reconectar signals
    signals.pre_save.connect(account_signals.validate_user_organization, sender=User)
    signals.pre_save.connect(account_signals.validate_organization_limits, sender=User)
    signals.pre_save.connect(account_signals.ensure_names_present, sender=User)
    signals.pre_save.connect(account_signals.validate_admin_without_org, sender=User)

@pytest.fixture
def mock_r2_storage(mocker):
    """Mock de Cloudflare R2 para tests de archivos"""
    mock_storage = mocker.Mock()
    mock_storage.save.return_value = 'test-file-key.jpg'
    mock_storage.url.return_value = 'https://r2.example.com/test-file-key.jpg'
    mock_storage.delete.return_value = True
    return mock_storage

@pytest.fixture(autouse=True)
def reset_cache(django_cache):
    """Limpia cache antes de cada test automáticamente"""
    django_cache.clear()
    yield
    django_cache.clear()

# 📁 Archivos de Prueba
@pytest.fixture
def sample_image():
    """Imagen JPG de prueba"""
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=b'\xFF\xD8\xFF\xE0',  # JPEG header
        content_type='image/jpeg'
    )

@pytest.fixture
def malicious_file():
    """Archivo malicioso para tests de seguridad"""
    return SimpleUploadedFile(
        name='malware.exe',
        content=b'MZ\x90\x00',  # DOS executable header
        content_type='application/x-msdownload'
    )
```

---

## 📊 ANÁLISIS DETALLADO DE TESTS IMPLEMENTADOS

### Resumen de Tests del Modelo User

**Archivo**: `tests/unit/test_accounts/test_models.py`  
**Total**: 33 tests | **Pasando**: 33/33 (100%) | **Tipo**: Unit Tests

**📚 DOCUMENTACIÓN DETALLADA**: Ver [`TESTS_DOCUMENTATION.md`](./TESTS_DOCUMENTATION.md) para:
- Análisis de cada uno de los 33 tests
- Qué valida cada test y por qué es importante
- Logs esperados en producción vs logs actuales
- Edge cases faltantes por cada test
- Ejemplos de código para tests de seguridad
- Matriz de cobertura detallada

### Distribución de Tests

| Clase | Tests | Propósito | Estado |
|-------|-------|-----------|--------|
| `TestUserCreation` | 5 | Validar creación de usuarios | ✅ 100% |
| `TestUserValidation` | 4 | Validar constraints de email/username | ✅ 100% |
| `TestUserPassword` | 5 | Validar hashing y verificación | ✅ 100% |
| `TestUserMethods` | 11 | Validar métodos del modelo | ✅ 100% |
| `TestUserSpecialFields` | 3 | Validar campos especiales | ✅ 100% |
| `TestUserDatabase` | 5 | Validar operaciones de BD | ✅ 100% |

### Cobertura Real vs Nominal

| Métrica | Valor | Estado |
|---------|-------|--------|
| Tests pasando | 33/33 | ✅ 100% |
| Líneas cubiertas (nominal) | ~300/620 | ⚠️ 48% |
| **Happy path** | 100% | ✅ Completo |
| **Edge cases** | 0% | ❌ No implementado |
| **Security tests** | 0% | ❌ No implementado |
| **Integration tests** | 0% | ❌ No implementado |
| **Logging tests** | 0% | ❌ No implementado |
| **Cobertura REAL** | ~26% | 🔴 Crítico |

---

## 🚨 TESTS FALTANTES (CRÍTICOS)

### Priorización por Impacto

```
🔴 CRÍTICO (Implementar AHORA)
├── Security Tests (15 tests)
│   ├── SQL Injection Prevention
│   ├── XSS Prevention
│   ├── Password Timing Attacks
│   ├── Brute Force Protection
│   └── Sensitive Data in Logs
│
├── Edge Cases (25 tests)
│   ├── Email Validation (max length, format, Unicode)
│   ├── Concurrent Operations
│   ├── Null/Empty Values
│   └── Special Characters
│
└── Integration Tests - Signals (12 tests)
    ├── ensure_names_present signal
    ├── validate_admin_without_org signal
    ├── validate_user_organization signal
    └── validate_organization_limits signal

🟠 ALTA (Implementar siguiente sprint)
├── Logging Tests (10 tests)
├── E2E Tests - API (8 tests)
└── Views Tests (15 tests)

🟡 MEDIA (Implementar después)
├── Forms Tests (10 tests)
├── Middleware Tests (8 tests)
└── Performance Tests (5 tests)
```

### Ejemplos de Tests Críticos Faltantes

**📚 DOCUMENTACIÓN COMPLETA**: Ver [`TESTS_DOCUMENTATION.md`](./TESTS_DOCUMENTATION.md) sección "Edge Cases Faltantes" para:
- 25 edge cases críticos con código completo
- Tests de seguridad (SQL injection, XSS, timing attacks)
- Tests de logging con verificación de formato
- Tests de integration con signals
- Tests de concurrencia y race conditions

**Resumen de Top 5 Más Críticos:**

```python
# 1. SQL Injection (CRÍTICO SEGURIDAD)
def test_email_sql_injection_prevented():
    malicious_email = "admin@example.com'; DROP TABLE users; --"
    user = User.objects.create_user(email=malicious_email, ...)
    assert User.objects.count() > 0  # Tabla no eliminada

# 2. Password Timing Attack (CRÍTICO SEGURIDAD)
def test_password_check_constant_time():
    # Verificar que check_password() toma tiempo constante
    # para prevenir timing attacks

# 3. Brute Force Protection (CRÍTICO SEGURIDAD)
def test_login_attempts_limited():
    # Después de 5 intentos fallidos debe bloquearse

# 4. Concurrent User Creation (CRÍTICO DATA INTEGRITY)
def test_concurrent_user_creation_race_condition():
    # 2 requests simultáneos con mismo email

# 5. Logs Never Contain Passwords (CRÍTICO SEGURIDAD)
def test_passwords_never_in_logs():
    # Verificar que contraseñas NUNCA aparecen en logs
```

---

## 📊 MATRIZ DE COBERTURA Y LOGGING

### Tabla de Cobertura Global

| Módulo | Unit Tests | Integration | E2E | Security | Logging | **Total** | **%** |
|--------|-----------|-------------|-----|----------|---------|-----------|-------|
| **accounts/models.py** | 33 | 0 | 0 | 0 | 0 | **33/128** | **26%** |
| accounts/views.py | 0 | 0 | 0 | 0 | 0 | 0/25 | 0% |
| accounts/forms.py | 0 | 0 | 0 | 0 | 0 | 0/10 | 0% |
| accounts/signals.py | 0 | 0 | 0 | 0 | 0 | 0/12 | 0% |
| orgs/models.py | 0 | 0 | 0 | 0 | 0 | 0/30 | 0% |
| orgs/storage_service.py | 0 | 0 | 0 | 0 | 0 | 0/20 | 0% |
| plans/models.py | 0 | 0 | 0 | 0 | 0 | 0/25 | 0% |
| plans/services.py | 0 | 0 | 0 | 0 | 0 | 0/30 | 0% |
| projects/models.py | 0 | 0 | 0 | 0 | 0 | 0/35 | 0% |
| files/security.py | 0 | 0 | 0 | 0 | 0 | 0/15 | 0% |
| **TOTAL** | **33** | **0** | **0** | **0** | **0** | **33/330** | **10%** |

### Matriz de Logging Implementado

| Evento | Nivel | Implementado en Código | Probado en Tests | Estado |
|--------|-------|------------------------|------------------|--------|
| `user_created` | INFO | ✅ Sí | ❌ No | 🟡 Parcial |
| `user_creation_failed` | ERROR | ✅ Sí | ❌ No | 🟡 Parcial |
| `login_successful` | INFO | ❌ No | ❌ No | 🔴 Falta |
| `login_failed` | WARNING | ❌ No | ❌ No | 🔴 Falta |
| `brute_force_detected` | ERROR | ❌ No | ❌ No | 🔴 Falta |
| `superuser_created` | WARNING | ❌ No | ❌ No | 🔴 Falta |
| `password_changed` | INFO | ❌ No | ❌ No | 🔴 Falta |
| `user_deleted` | WARNING | ❌ No | ❌ No | 🔴 Falta |

**Conclusión**: Solo 2/8 eventos críticos tienen logging, y NINGUNO está probado.

---

**Problema 2: Límite de usuarios en organización** ✅ RESUELTO
- **Error**: `ValidationError: ['La organización ha alcanzado su límite de usuarios']`
- **Solución**: Usar fixture `disable_account_signals`

**Problema 3: Logging conflict** ✅ RESUELTO
- **Error**: `KeyError: "Attempt to overwrite 'message' in LogRecord"`
- **Solución**: Modificado `structured_logging.py` para usar `'detail'` en lugar de `'message'` en el dict extra para evitar conflicto con LogRecord de Python

### 🎯 Próximos Pasos Inmediatos

1. ✅ **Arreglar tests existentes** - COMPLETADO
   - ✅ Agregado `disable_account_signals` a todos los tests que lo necesitan
   - ✅ Solucionado el error de logging en structured_logging.py
   - ✅ **RESULTADO: 33/33 tests pasando (100%)** 🎉

2. **Completar factories básicas**:
   - PlanFactory
   - SubscriptionFactory
   - ProjectFactory
   - FileUploadFactory

3. **Expandir tests de User**:
   - Tests de integración con Organization
   - Tests de permisos más complejos

---

## 📚 Tabla de Contenidos

1. [Stack de Testing](#stack-de-testing)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Configuración Inicial](#configuración-inicial)
4. [Plan de Implementación por Fases](#plan-de-implementación-por-fases)
5. [Guía de Testing por Módulo](#guía-de-testing-por-módulo)
6. [Patrones y Mejores Prácticas](#patrones-y-mejores-prácticas)
7. [Comandos Útiles](#comandos-útiles)
8. [Métricas y Objetivos](#métricas-y-objetivos)
9. [Checklist de Progreso](#checklist-de-progreso)

---

## 🛠️ Stack de Testing

### Dependencias Principales

```txt
# Testing Framework
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
pytest-xdist==3.5.0  # Para ejecutar tests en paralelo

# Generación de Datos
factory-boy==3.3.0
faker==20.1.0

# Utilities
freezegun==1.4.0  # Mock de fechas/tiempo
pytest-mock==3.12.0  # Mocking avanzado
responses==0.24.1  # Mock de requests HTTP
```

### Instalación

```bash
pip install pytest pytest-django pytest-cov pytest-xdist factory-boy faker freezegun pytest-mock responses
```

---

## 📁 Estructura de Archivos

### Estructura Completa del Directorio `tests/`

```
tests/
├── __init__.py
├── conftest.py                          # Configuración global de pytest y fixtures
├── pytest.ini                           # Configuración de pytest (crear en raíz)
├── .coveragerc                          # Configuración de coverage (crear en raíz)
│
├── factories/                           # Factory Boy factories para crear objetos de prueba
│   ├── __init__.py
│   ├── account_factories.py             # User, CustomUser
│   ├── org_factories.py                 # Organization, OrganizationMember
│   ├── project_factories.py             # Project, ProjectMember, Transaction
│   ├── plan_factories.py                # Plan, Subscription
│   └── file_factories.py                # FileUpload, etc.
│
├── fixtures/                            # Datos estáticos de prueba
│   ├── sample_files/                    # Archivos de ejemplo para tests de upload
│   │   ├── test_image.jpg
│   │   ├── test_document.pdf
│   │   └── test_archive.zip
│   └── test_data.json                   # JSON con datos de prueba
│
├── unit/                                # Tests unitarios (funciones aisladas)
│   ├── __init__.py
│   │
│   ├── test_accounts/
│   │   ├── __init__.py
│   │   ├── test_models.py               # CustomUser model tests
│   │   ├── test_views.py                # Login, register, profile views
│   │   ├── test_forms.py                # User forms validation
│   │   ├── test_middleware.py           # Auth middleware
│   │   ├── test_signals.py              # User signals (post_save, etc)
│   │   └── test_cache_signals.py        # Cache invalidation
│   │
│   ├── test_orgs/
│   │   ├── __init__.py
│   │   ├── test_models.py               # Organization, OrganizationMember
│   │   ├── test_views.py                # Org CRUD, member management
│   │   ├── test_forms.py                # Organization forms
│   │   ├── test_storage_service.py      # R2/S3 storage service
│   │   ├── test_cache_utils.py          # Cache utilities
│   │   ├── test_decorators.py           # @require_org_member, etc
│   │   └── test_middleware.py           # Org-based middleware
│   │
│   ├── test_plans/
│   │   ├── __init__.py
│   │   ├── test_models.py               # Plan, Subscription, PlanFeature
│   │   ├── test_services.py             # Subscription logic, upgrades
│   │   ├── test_views.py                # Plan selection, checkout
│   │   ├── test_middleware.py           # Plan enforcement
│   │   └── test_signals.py              # Subscription lifecycle signals
│   │
│   ├── test_projects/
│   │   ├── __init__.py
│   │   ├── test_models.py               # Project, ProjectMember, Transaction
│   │   ├── test_views.py                # Project CRUD, finance views
│   │   ├── test_forms.py                # Project and transaction forms
│   │   ├── test_services.py             # Business logic
│   │   ├── test_finance_cache.py        # Financial calculations cache
│   │   └── test_managers.py             # Custom QuerySet managers
│   │
│   ├── test_files/
│   │   ├── __init__.py
│   │   ├── test_models.py               # FileUpload model
│   │   ├── test_views.py                # Upload, download, delete
│   │   ├── test_api.py                  # File API endpoints
│   │   ├── test_security.py             # File validation, malware scan
│   │   ├── test_storage_signals.py      # File storage signals
│   │   ├── test_validators.py           # File type/size validators
│   │   └── test_managers.py             # File managers
│   │
│   ├── test_main/
│   │   ├── __init__.py
│   │   ├── test_views.py                # Dashboard, landing page
│   │   └── test_middleware.py           # Main middleware
│   │
│   ├── test_users/
│   │   ├── __init__.py
│   │   ├── test_models.py               # User profile models
│   │   └── test_views.py                # User profile views
│   │
│   └── test_core/
│       ├── __init__.py
│       ├── test_middleware.py           # Core middleware
│       ├── test_validators.py           # Custom validators
│       ├── test_email_utils.py          # Email sending
│       ├── test_error_handlers.py       # Error handling
│       ├── test_upload_handlers.py      # File upload handlers
│       └── test_health.py               # Health check endpoint
│
├── integration/                         # Tests de integración (múltiples componentes)
│   ├── __init__.py
│   ├── test_user_onboarding.py          # Flujo completo: registro → org → plan
│   ├── test_subscription_workflow.py    # Plan selection → payment → activation
│   ├── test_project_lifecycle.py        # Create → add members → transactions → close
│   ├── test_file_upload_workflow.py     # Upload → validate → store → retrieve
│   └── test_org_storage_limits.py       # Storage quota enforcement
│
├── e2e/                                 # Tests end-to-end (opcional, con Selenium/Playwright)
│   ├── __init__.py
│   └── test_critical_paths.py
│
└── performance/                         # Tests de rendimiento (opcional)
    ├── __init__.py
    └── test_query_performance.py
```

---

## ⚙️ Configuración Inicial

### 1. Archivo `pytest.ini` (Raíz del proyecto)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=arc_manager
    --cov-report=html
    --cov-report=term-missing:skip-covered
    --cov-fail-under=80
    --maxfail=5
    --reuse-db
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    smoke: marks tests as smoke tests (critical paths)
    wip: marks tests as work in progress
testpaths = tests
```

### 2. Archivo `.coveragerc` (Raíz del proyecto)

```ini
[run]
source = arc_manager
omit = 
    */migrations/*
    */tests/*
    */test_*.py
    */__pycache__/*
    */settings.py
    */wsgi.py
    */asgi.py
    manage.py
    */venv/*
    */virtualenv/*

[report]
precision = 2
show_missing = True
skip_covered = False

exclude_lines =
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if settings.DEBUG:
    if TYPE_CHECKING:
    @abstract
    @abc.abstractmethod

[html]
directory = htmlcov
```

### 3. Archivo `tests/conftest.py` (Fixtures globales)

```python
"""
Configuración global de pytest y fixtures compartidas
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from faker import Faker

fake = Faker()
User = get_user_model()


# ============================================================================
# FIXTURES DE BASE DE DATOS
# ============================================================================

@pytest.fixture
def api_client():
    """Cliente de Django para hacer requests"""
    return Client()


@pytest.fixture
def authenticated_client(db, user):
    """Cliente autenticado con un usuario"""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def user(db):
    """Usuario básico para tests"""
    return User.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password='testpass123'
    )


@pytest.fixture
def superuser(db):
    """Superusuario para tests de admin"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


# ============================================================================
# FIXTURES DE ARCHIVOS
# ============================================================================

@pytest.fixture
def sample_image():
    """Imagen de prueba"""
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=b'\x47\x49\x46\x38\x39\x61',  # GIF header
        content_type='image/jpeg'
    )


@pytest.fixture
def sample_pdf():
    """PDF de prueba"""
    return SimpleUploadedFile(
        name='test_document.pdf',
        content=b'%PDF-1.4',
        content_type='application/pdf'
    )


@pytest.fixture
def malicious_file():
    """Archivo malicioso de prueba"""
    return SimpleUploadedFile(
        name='malware.exe',
        content=b'MZ\x90\x00',  # DOS executable header
        content_type='application/x-msdownload'
    )


# ============================================================================
# FIXTURES DE CONFIGURACIÓN
# ============================================================================

@pytest.fixture
def mock_r2_storage(mocker):
    """Mock del storage de Cloudflare R2"""
    mock_storage = mocker.Mock()
    mock_storage.save.return_value = 'test-file-key.jpg'
    mock_storage.url.return_value = 'https://r2.example.com/test-file-key.jpg'
    return mock_storage


@pytest.fixture(autouse=True)
def reset_cache(django_cache):
    """Limpiar cache antes de cada test"""
    django_cache.clear()


# ============================================================================
# MARKERS ÚTILES
# ============================================================================

def pytest_configure(config):
    """Registrar markers personalizados"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
```

---

## 📅 Plan de Implementación por Fases

### **FASE 1: Fundamentos y Modelos Críticos** (Semana 1-2)

#### Objetivo
Establecer la base de testing y cubrir los modelos más críticos del negocio.

#### Tareas
1. ✅ **Setup Inicial**
   - Instalar dependencias de testing
   - Crear `pytest.ini`, `.coveragerc`, `conftest.py`
   - Configurar CI/CD con GitHub Actions

2. ✅ **Factories Base** (Prioridad: ALTA)
   - `tests/factories/account_factories.py` → UserFactory
   - `tests/factories/org_factories.py` → OrganizationFactory, MemberFactory
   - `tests/factories/plan_factories.py` → PlanFactory, SubscriptionFactory
   - `tests/factories/project_factories.py` → ProjectFactory, TransactionFactory

3. ✅ **Tests de Modelos** (Prioridad: ALTA)
   - `test_accounts/test_models.py` → User creation, authentication
   - `test_orgs/test_models.py` → Organization, members, permissions
   - `test_plans/test_models.py` → Plan features, subscription validation
   - `test_projects/test_models.py` → Project, transactions, calculations

#### Entregables
- [ ] 4 archivos de factories completos
- [ ] 4 archivos de test_models.py con >80% coverage
- [ ] Configuración CI/CD funcionando
- [ ] Reporte de coverage inicial

---

### **FASE 2: Servicios y Lógica de Negocio** (Semana 3)

#### Objetivo
Probar la lógica de negocio crítica que maneja datos financieros y suscripciones.

#### Tareas
1. ✅ **Tests de Servicios de Planes** (Prioridad: CRÍTICA)
   - `test_plans/test_services.py`
     - Creación de suscripciones
     - Upgrades/downgrades de planes
     - Cálculo de prorated charges
     - Validación de límites de plan

2. ✅ **Tests de Servicios de Proyectos** (Prioridad: ALTA)
   - `test_projects/test_services.py`
     - Creación de proyectos
     - Gestión de miembros
     - Cálculos financieros (ingresos, gastos, balance)
     - Validaciones de permisos

3. ✅ **Tests de Storage Service** (Prioridad: ALTA)
   - `test_orgs/test_storage_service.py`
     - Upload a R2/S3
     - Download de archivos
     - Eliminación de archivos
     - Validación de quotas

4. ✅ **Tests de Cache** (Prioridad: MEDIA)
   - `test_projects/test_finance_cache.py`
   - `test_orgs/test_cache_utils.py`
     - Invalidación de cache
     - Cache hit/miss scenarios
     - Cache warming

#### Entregables
- [ ] 4 archivos de tests de servicios completos
- [ ] Coverage >85% en servicios críticos
- [ ] Documentación de casos edge detectados

---

### **FASE 3: Seguridad y Archivos** (Semana 4)

#### Objetivo
Asegurar que el sistema de archivos sea seguro y robusto.

#### Tareas
1. ✅ **Tests de Seguridad de Archivos** (Prioridad: CRÍTICA)
   - `test_files/test_security.py`
     - Validación de tipos de archivo
     - Detección de malware
     - Validación de tamaño
     - Sanitización de nombres de archivo
     - Path traversal prevention

2. ✅ **Tests de File Models y Managers** (Prioridad: ALTA)
   - `test_files/test_models.py`
   - `test_files/test_managers.py`
     - CRUD de archivos
     - Soft delete
     - Permisos de acceso
     - Metadatos

3. ✅ **Tests de File API** (Prioridad: ALTA)
   - `test_files/test_api.py`
     - Upload endpoint
     - Download endpoint
     - Delete endpoint
     - List/search endpoints
     - Rate limiting

4. ✅ **Tests de Validators** (Prioridad: MEDIA)
   - `test_files/test_validators.py`
   - `test_core/test_validators.py`
     - Custom field validators
     - File validators
     - Business rule validators

#### Entregables
- [ ] Suite completa de tests de seguridad
- [ ] Tests de todos los endpoints de archivos
- [ ] Coverage >90% en módulo files

---

### **FASE 4: Vistas y Middleware** (Semana 5)

#### Objetivo
Probar las capas de presentación y middleware.

#### Tareas
1. ✅ **Tests de Vistas de Accounts** (Prioridad: ALTA)
   - `test_accounts/test_views.py`
     - Login/logout
     - Registro
     - Password reset
     - Profile edit
     - 2FA (si existe)

2. ✅ **Tests de Vistas de Organizations** (Prioridad: ALTA)
   - `test_orgs/test_views.py`
     - Org CRUD
     - Member management
     - Settings

3. ✅ **Tests de Vistas de Projects** (Prioridad: MEDIA)
   - `test_projects/test_views.py`
     - Project CRUD
     - Dashboard
     - Finance views

4. ✅ **Tests de Middleware** (Prioridad: ALTA)
   - `test_accounts/test_middleware.py`
   - `test_orgs/test_middleware.py`
   - `test_plans/test_middleware.py`
   - `test_core/test_middleware.py`
     - Authentication middleware
     - Organization context
     - Plan enforcement
     - Error handling

#### Entregables
- [ ] Tests de todas las vistas principales
- [ ] Tests de todos los middlewares
- [ ] Coverage >75% en vistas

---

### **FASE 5: Integración y Signals** (Semana 6)

#### Objetivo
Probar flujos completos y signals del sistema.

#### Tareas
1. ✅ **Tests de Signals** (Prioridad: MEDIA)
   - `test_accounts/test_signals.py`
   - `test_orgs/test_signals.py`
   - `test_projects/test_signals.py`
   - `test_files/test_storage_signals.py`
     - Post-save signals
     - Pre-delete signals
     - Cache invalidation signals

2. ✅ **Tests de Integración** (Prioridad: ALTA)
   - `integration/test_user_onboarding.py`
     - Registro → Email verification → Org creation → Plan selection
   - `integration/test_subscription_workflow.py`
     - Plan selection → Payment → Activation → Usage → Upgrade
   - `integration/test_project_lifecycle.py`
     - Create project → Add members → Add transactions → Generate reports → Close
   - `integration/test_file_upload_workflow.py`
     - Upload → Validate → Store → Share → Download → Delete

3. ✅ **Tests de Forms** (Prioridad: BAJA)
   - `test_accounts/test_forms.py`
   - `test_orgs/test_forms.py`
   - `test_projects/test_forms.py`
     - Validación de campos
     - Custom clean methods
     - Form save logic

#### Entregables
- [ ] 4 flujos de integración completos
- [ ] Tests de todos los signals importantes
- [ ] Coverage global >80%

---

### **FASE 6: Refinamiento y Performance** (Semana 7)

#### Objetivo
Optimizar tests y agregar tests de rendimiento.

#### Tareas
1. ✅ **Optimización de Tests**
   - Identificar tests lentos
   - Agregar `@pytest.mark.slow`
   - Paralelizar ejecución con pytest-xdist
   - Optimizar fixtures

2. ✅ **Tests de Performance** (Prioridad: BAJA)
   - `performance/test_query_performance.py`
     - N+1 query detection
     - Pagination performance
     - Cache effectiveness

3. ✅ **Tests de Management Commands** (Prioridad: BAJA)
   - Tests de comandos en `management/commands/`

4. ✅ **Smoke Tests** (Prioridad: ALTA)
   - `test_mvp_ready.py` (ya existe)
   - Ampliar con más checks críticos

#### Entregables
- [ ] Tests ejecutándose en <2 minutos
- [ ] Tests de performance para queries críticos
- [ ] Suite de smoke tests completa

---

## 📖 Guía de Testing por Módulo

### 🔐 **accounts/** - Testing Guide

#### Componentes a Testear
- **Models**: CustomUser, UserProfile
- **Views**: Login, Register, Logout, PasswordReset, Profile
- **Forms**: UserCreationForm, UserChangeForm, PasswordResetForm
- **Middleware**: AuthenticationMiddleware, LoginRequiredMiddleware
- **Signals**: post_save (crear perfil), pre_delete
- **Cache Signals**: Invalidación de cache de usuario

#### Casos de Test Críticos

```python
# test_accounts/test_models.py
def test_user_creation_with_valid_data()
def test_user_creation_with_duplicate_email()
def test_user_password_is_hashed()
def test_user_string_representation()
def test_user_get_full_name()
def test_user_profile_created_on_user_creation()  # Signal

# test_accounts/test_views.py
def test_login_with_valid_credentials()
def test_login_with_invalid_credentials()
def test_login_redirects_to_dashboard()
def test_logout_clears_session()
def test_register_creates_user_and_profile()
def test_register_with_invalid_email()
def test_password_reset_sends_email()
def test_profile_update_changes_user_data()
def test_unauthenticated_user_redirected_to_login()

# test_accounts/test_middleware.py
def test_middleware_allows_authenticated_user()
def test_middleware_redirects_unauthenticated_user()
def test_middleware_allows_whitelisted_paths()

# test_accounts/test_signals.py
def test_user_profile_created_automatically()
def test_cache_invalidated_on_user_update()
```

#### Coverage Target
- Models: 95%+
- Views: 85%+
- Middleware: 90%+

---

### 🏢 **orgs/** - Testing Guide

#### Componentes a Testear
- **Models**: Organization, OrganizationMember, OrganizationInvitation
- **Views**: OrgCRUD, MemberManagement, Settings
- **Storage Service**: R2/S3 operations
- **Cache Utils**: Invalidación de cache de org
- **Decorators**: @require_org_member, @org_admin_required
- **Middleware**: OrganizationMiddleware

#### Casos de Test Críticos

```python
# test_orgs/test_models.py
def test_organization_creation()
def test_organization_slug_auto_generation()
def test_organization_member_roles()
def test_member_has_permission()
def test_organization_storage_usage_calculation()
def test_organization_member_count()

# test_orgs/test_storage_service.py
def test_upload_file_to_r2()
def test_upload_file_exceeds_quota()
def test_download_file_from_r2()
def test_delete_file_from_r2()
def test_get_presigned_url()
def test_storage_quota_enforcement()

# test_orgs/test_decorators.py
def test_require_org_member_allows_member()
def test_require_org_member_denies_non_member()
def test_org_admin_required_allows_admin()
def test_org_admin_required_denies_regular_member()

# test_orgs/test_cache_utils.py
def test_cache_invalidation_on_org_update()
def test_cache_invalidation_on_member_add()
def test_cache_key_generation()
```

#### Coverage Target
- Models: 95%+
- Storage Service: 90%+
- Decorators: 100%
- Cache Utils: 85%+

---

### 💳 **plans/** - Testing Guide

#### Componentes a Testear
- **Models**: Plan, Subscription, PlanFeature, SubscriptionUsage
- **Services**: SubscriptionService (create, upgrade, downgrade, cancel)
- **Views**: PlanSelection, Checkout, Manage
- **Middleware**: PlanEnforcementMiddleware
- **Signals**: subscription_created, subscription_cancelled

#### Casos de Test Críticos

```python
# test_plans/test_models.py
def test_plan_has_features()
def test_subscription_is_active()
def test_subscription_is_expired()
def test_subscription_can_use_feature()
def test_subscription_feature_limit_reached()
def test_plan_price_calculation()

# test_plans/test_services.py
def test_create_subscription()
def test_upgrade_subscription_prorated_charge()
def test_downgrade_subscription_credit()
def test_cancel_subscription()
def test_subscription_renewal()
def test_trial_period_handling()
def test_feature_usage_tracking()
def test_plan_limit_enforcement()

# test_plans/test_middleware.py
def test_middleware_allows_user_within_plan_limits()
def test_middleware_blocks_user_exceeding_limits()
def test_middleware_redirects_to_upgrade_page()
```

#### Coverage Target
- Models: 95%+
- Services: 95%+ (CRÍTICO)
- Middleware: 90%+

---

### 📊 **projects/** - Testing Guide

#### Componentes a Testear
- **Models**: Project, ProjectMember, Transaction, Category
- **Services**: ProjectService, FinanceService
- **Views**: ProjectCRUD, Dashboard, Reports
- **Finance Cache**: Cálculos de balance, ingresos, gastos
- **Forms**: ProjectForm, TransactionForm

#### Casos de Test Críticos

```python
# test_projects/test_models.py
def test_project_creation()
def test_project_member_roles()
def test_transaction_updates_project_balance()
def test_project_total_income()
def test_project_total_expenses()
def test_project_balance_calculation()
def test_project_soft_delete()

# test_projects/test_services.py
def test_create_project_with_members()
def test_add_transaction_updates_cache()
def test_transfer_between_projects()
def test_close_project()
def test_generate_financial_report()

# test_projects/test_finance_cache.py
def test_balance_cached_after_calculation()
def test_cache_invalidated_on_new_transaction()
def test_cache_invalidated_on_transaction_update()
def test_cache_miss_recalculates()
def test_concurrent_cache_access()

# test_projects/test_views.py
def test_dashboard_shows_correct_data()
def test_project_list_filtered_by_org()
def test_transaction_form_validation()
def test_export_transactions_csv()
```

#### Coverage Target
- Models: 95%+
- Services: 90%+
- Finance Cache: 95%+ (CRÍTICO)

---

### 📁 **files/** - Testing Guide

#### Componentes a Testear
- **Models**: FileUpload, FileVersion
- **API**: Upload, Download, Delete endpoints
- **Security**: Validation, Malware scanning
- **Validators**: Type, Size, Content validators
- **Storage Signals**: Pre/post upload/delete
- **Managers**: FileManager (soft delete, filtering)

#### Casos de Test Críticos

```python
# test_files/test_security.py
def test_validate_allowed_file_type()
def test_reject_executable_file()
def test_reject_oversized_file()
def test_sanitize_filename()
def test_detect_malicious_content()
def test_prevent_path_traversal()
def test_validate_file_extension_vs_content()

# test_files/test_models.py
def test_file_upload_with_valid_file()
def test_file_size_stored_correctly()
def test_file_mime_type_detection()
def test_file_belongs_to_organization()
def test_file_soft_delete()
def test_file_version_creation()

# test_files/test_api.py
def test_upload_file_authenticated()
def test_upload_file_unauthenticated_denied()
def test_download_file_with_permission()
def test_download_file_without_permission()
def test_delete_file_by_owner()
def test_delete_file_by_non_owner_denied()
def test_list_files_paginated()

# test_files/test_validators.py
def test_file_size_validator()
def test_file_extension_validator()
def test_image_dimension_validator()
def test_video_duration_validator()
```

#### Coverage Target
- Security: 100% (CRÍTICO)
- API: 90%+
- Models: 95%+
- Validators: 95%+

---

### 🏠 **main/** - Testing Guide

#### Componentes a Testear
- **Views**: Home, Dashboard, About
- **Middleware**: MaintenanceMode, SecurityHeaders
- **Signals**: Analytics tracking

#### Casos de Test Críticos

```python
# test_main/test_views.py
def test_home_page_loads()
def test_dashboard_requires_authentication()
def test_dashboard_shows_user_data()
def test_about_page_loads()

# test_main/test_middleware.py
def test_maintenance_mode_blocks_requests()
def test_maintenance_mode_allows_superusers()
def test_security_headers_present()
```

#### Coverage Target
- Views: 80%+
- Middleware: 90%+

---

### ⚙️ **core/** - Testing Guide

#### Componentes a Testear
- **Email Utils**: send_email, send_templated_email
- **Error Handlers**: 404, 500, 403 handlers
- **Upload Handlers**: ChunkedUploadHandler
- **Validators**: Custom validators
- **Health Check**: Health endpoint

#### Casos de Test Críticos

```python
# test_core/test_email_utils.py
def test_send_email_success()
def test_send_email_with_attachment()
def test_send_templated_email()
def test_email_failure_logged()

# test_core/test_error_handlers.py
def test_404_handler_returns_custom_page()
def test_500_handler_logs_error()
def test_403_handler_shows_permission_denied()

# test_core/test_upload_handlers.py
def test_chunked_upload_handler()
def test_upload_handler_validates_size()

# test_core/test_health.py
def test_health_endpoint_returns_200()
def test_health_check_database_connection()
def test_health_check_cache_connection()
```

#### Coverage Target
- Email Utils: 85%+
- Error Handlers: 90%+
- Validators: 95%+

---

## 🎯 Patrones y Mejores Prácticas

### 1. Naming Conventions

```python
# ✅ GOOD
def test_user_creation_with_valid_email()
def test_login_fails_with_invalid_password()
def test_subscription_upgrade_calculates_prorated_charge()

# ❌ BAD
def test1()
def test_user()
def test_stuff()
```

### 2. Arrange-Act-Assert (AAA Pattern)

```python
def test_user_can_create_project():
    # ARRANGE - Setup test data
    user = UserFactory()
    org = OrganizationFactory(owner=user)
    
    # ACT - Execute the action
    project = Project.objects.create(
        name="Test Project",
        organization=org,
        created_by=user
    )
    
    # ASSERT - Verify the result
    assert project.name == "Test Project"
    assert project.organization == org
    assert project.created_by == user
    assert Project.objects.count() == 1
```

### 3. Use Factories, Not Fixtures

```python
# ✅ GOOD - Flexible, readable, maintainable
def test_project_with_members():
    project = ProjectFactory(
        name="My Project",
        members__count=3  # Creates 3 members automatically
    )
    assert project.members.count() == 3

# ❌ BAD - Rigid, hard to maintain
def test_project_with_members():
    # Loading from JSON fixture
    call_command('loaddata', 'test_projects.json')
    project = Project.objects.get(id=1)
    assert project.members.count() == 3
```

### 4. Test One Thing Per Test

```python
# ✅ GOOD
def test_user_email_is_unique():
    UserFactory(email="test@example.com")
    with pytest.raises(IntegrityError):
        UserFactory(email="test@example.com")

def test_user_password_is_hashed():
    user = UserFactory(password="plaintext")
    assert user.password != "plaintext"
    assert user.check_password("plaintext")

# ❌ BAD - Testing multiple things
def test_user_validation():
    user = UserFactory(email="test@example.com")
    assert user.password != "plaintext"
    with pytest.raises(IntegrityError):
        UserFactory(email="test@example.com")
    assert user.is_active
```

### 5. Mock External Services

```python
# ✅ GOOD - Mock S3/R2 storage
def test_file_upload_to_storage(mocker):
    mock_storage = mocker.patch('apps.orgs.storage_service.R2Storage')
    mock_storage.save.return_value = 'file-key-123'
    
    file = FileUploadFactory()
    
    assert file.storage_key == 'file-key-123'
    mock_storage.save.assert_called_once()

# ❌ BAD - Actually hitting R2 (slow, flaky, costs money)
def test_file_upload_to_storage():
    file = FileUploadFactory()
    # This actually uploads to R2!
    assert file.storage_key is not None
```

### 6. Use Parametrize for Similar Tests

```python
# ✅ GOOD
@pytest.mark.parametrize("role,can_delete", [
    ("owner", True),
    ("admin", True),
    ("member", False),
    ("viewer", False),
])
def test_project_deletion_permissions(role, can_delete):
    project = ProjectFactory()
    user = UserFactory()
    ProjectMemberFactory(project=project, user=user, role=role)
    
    assert user.can_delete_project(project) == can_delete

# ❌ BAD - Repetitive
def test_owner_can_delete_project():
    ...
def test_admin_can_delete_project():
    ...
def test_member_cannot_delete_project():
    ...
def test_viewer_cannot_delete_project():
    ...
```

### 7. Test Edge Cases and Exceptions

```python
def test_subscription_upgrade():
    # Happy path
    subscription = SubscriptionFactory(plan__name="Basic")
    subscription.upgrade(plan=Plan.objects.get(name="Pro"))
    assert subscription.plan.name == "Pro"
    
def test_subscription_upgrade_to_same_plan_raises_error():
    # Edge case
    subscription = SubscriptionFactory(plan__name="Basic")
    basic_plan = subscription.plan
    
    with pytest.raises(ValueError, match="Already on this plan"):
        subscription.upgrade(plan=basic_plan)

def test_subscription_upgrade_from_higher_to_lower_raises_error():
    # Edge case
    subscription = SubscriptionFactory(plan__name="Enterprise")
    basic_plan = Plan.objects.get(name="Basic")
    
    with pytest.raises(ValueError, match="Use downgrade instead"):
        subscription.upgrade(plan=basic_plan)
```

### 8. Use Markers for Organization

```python
@pytest.mark.unit
def test_user_model_str():
    user = UserFactory(username="johndoe")
    assert str(user) == "johndoe"

@pytest.mark.integration
def test_user_onboarding_flow():
    # Register → Verify Email → Create Org → Select Plan
    ...

@pytest.mark.slow
def test_large_data_export():
    # This test takes 30+ seconds
    ...

@pytest.mark.wip
def test_new_feature_in_development():
    # Work in progress, might fail
    ...
```

### 9. Clean Up After Tests

```python
# ✅ GOOD - Using pytest fixtures with yield
@pytest.fixture
def temp_file():
    file_path = '/tmp/test_file.txt'
    with open(file_path, 'w') as f:
        f.write('test content')
    
    yield file_path  # Test runs here
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)

# ✅ GOOD - Using context managers
def test_file_processing():
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b'test data')
        tmp.flush()
        process_file(tmp.name)
        # File automatically deleted after block
```

### 10. Test Database Queries (N+1 Detection)

```python
def test_project_list_does_not_have_n_plus_1_queries(django_assert_num_queries):
    # Create 10 projects with members
    ProjectFactory.create_batch(10, members__count=5)
    
    # Should use select_related/prefetch_related to avoid N+1
    with django_assert_num_queries(3):  # Adjust based on expected queries
        projects = Project.objects.with_members().all()
        list(projects)  # Force evaluation
```

---

## 🚀 COMANDOS ÚTILES

### Ejecutar Tests en Docker

```bash
# ========================================
# COMANDOS PRINCIPALES (Uso diario)
# ========================================

# Ejecutar TODOS los tests
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v"

# Ejecutar solo tests UNIT (rápidos, sin signals)
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/ -v -m unit"

# Ejecutar solo tests INTEGRATION (con signals y BD)
docker-compose exec web bash -c "cd /app && python -m pytest tests/integration/ -v -m integration"

# Ejecutar solo tests del modelo User
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/test_models.py -v"

# Ejecutar UN test específico
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/test_models.py::TestUserCreation::test_user_creation_with_factory -v"

# Ejecutar SIN coverage (MÁS RÁPIDO para desarrollo)
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/test_models.py -v --no-cov"

# ========================================
# COVERAGE Y REPORTES
# ========================================

# Ejecutar con coverage HTML
docker-compose exec web bash -c "cd /app && python -m pytest tests/ --cov=arc_manager --cov-report=html"
# Ver reporte en: htmlcov/index.html

# Coverage en terminal con líneas faltantes
docker-compose exec web bash -c "cd /app && python -m pytest tests/ --cov=arc_manager --cov-report=term-missing"

# Coverage de un módulo específico
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/ --cov=arc_manager.apps.accounts --cov-report=term-missing"

# Fallar si coverage < 80%
docker-compose exec web bash -c "cd /app && python -m pytest tests/ --cov=arc_manager --cov-fail-under=80"

# ========================================
# DEBUGGING Y DESARROLLO
# ========================================

# Mostrar prints en tests (útil para debugging)
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v -s"

# Parar en el PRIMER fallo
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v -x"

# Parar después de 3 fallos
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v --maxfail=3"

# Re-ejecutar solo tests que FALLARON la última vez
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v --lf"

# Ver los 10 tests MÁS LENTOS
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v --durations=10"

# Ejecutar con debugger (pdb) al fallar
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v --pdb"

# ========================================
# FILTRADO POR MARKERS
# ========================================

# Solo tests UNIT
docker-compose exec web bash -c "cd /app && python -m pytest -m unit -v"

# Solo tests INTEGRATION
docker-compose exec web bash -c "cd /app && python -m pytest -m integration -v"

# Solo tests SECURITY
docker-compose exec web bash -c "cd /app && python -m pytest -m security -v"

# Excluir tests LENTOS
docker-compose exec web bash -c "cd /app && python -m pytest -m 'not slow' -v"

# Unit tests que NO son lentos
docker-compose exec web bash -c "cd /app && python -m pytest -m 'unit and not slow' -v"

# Integration O Smoke tests
docker-compose exec web bash -c "cd /app && python -m pytest -m 'integration or smoke' -v"

# ========================================
# PERFORMANCE
# ========================================

# Ejecutar tests en PARALELO (4 workers)
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v -n 4"

# Reusar BD entre ejecuciones (más rápido)
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v --reuse-db"

# ========================================
# ANÁLISIS Y REPORTES
# ========================================

# Listar todos los tests disponibles (sin ejecutar)
docker-compose exec web bash -c "cd /app && python -m pytest --collect-only tests/"

# Ver todos los markers disponibles
docker-compose exec web bash -c "cd /app && python -m pytest --markers"

# Ver fixtures disponibles
docker-compose exec web bash -c "cd /app && python -m pytest --fixtures"

# Modo SUPER verbose (mucho output)
docker-compose exec web bash -c "cd /app && python -m pytest tests/ -vv"
```

### Shortcuts Recomendados (para tu .bashrc o alias)

```bash
# Agregar a ~/.bashrc o ~/.zshrc:

alias dt='docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v"'
alias dtu='docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/ -v -m unit"'
alias dti='docker-compose exec web bash -c "cd /app && python -m pytest tests/integration/ -v -m integration"'
alias dtc='docker-compose exec web bash -c "cd /app && python -m pytest tests/ --cov=arc_manager --cov-report=term-missing"'
alias dtf='docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v -x"'  # Stop on first failure
alias dtl='docker-compose exec web bash -c "cd /app && python -m pytest tests/ -v --lf"'  # Last failed

# Uso:
# dt          → Ejecutar todos los tests
# dtu         → Solo unit tests
# dti         → Solo integration tests
# dtc         → Tests con coverage
# dtf         → Parar al primer fallo
# dtl         → Re-ejecutar lo que falló
```

---

## 📊 MÉTRICAS Y OBJETIVOS

### Objetivos de Coverage por Componente

| Componente                     | Coverage Objetivo | Coverage Actual | Prioridad | Notas                          |
|--------------------------------|-------------------|-----------------|-----------|--------------------------------|
| **Models**                     | >80%              | ~48%            | 🔴 ALTA    | User: 48%, resto sin coverage  |
| `accounts.models`              | >85%              | ~48%            | 🔴 ALTA    | 33 tests User, faltan signals  |
| `orgs.models`                  | >80%              | ~0%             | 🔴 ALTA    | 0 tests                        |
| `plans.models`                 | >85%              | ~0%             | 🔴 ALTA    | Crítico para billing           |
| `projects.models`              | >80%              | ~0%             | 🔴 ALTA    | 0 tests                        |
| `files.models`                 | >75%              | ~0%             | 🟡 MEDIA   | 0 tests                        |
| **Services/Utils**             | >85%              | ~0%             | 🔴 ALTA    | Lógica de negocio crítica      |
| `plans.services`               | >90%              | ~0%             | 🔴 ALTA    | Maneja facturación             |
| `projects.services`            | >85%              | ~0%             | 🔴 ALTA    | Transacciones financieras      |
| `orgs.storage_service`         | >85%              | ~0%             | 🔴 ALTA    | S3/R2 uploads                  |
| `projects.finance_cache`       | >90%              | ~0%             | 🔴 ALTA    | Cache de balances              |
| `orgs.cache_utils`             | >80%              | ~0%             | 🟡 MEDIA   | Cache de organizaciones        |
| **Security/Validators**        | >95%              | ~0%             | 🔴 ALTA    | Máxima prioridad               |
| `files.security`               | 100%              | ~0%             | 🔴 ALTA    | Path traversal, MIME, size     |
| `files.validators`             | >90%              | ~0%             | 🔴 ALTA    | Validación uploads             |
| `core.validators`              | >90%              | ~0%             | 🔴 ALTA    | Validaciones globales          |
| **Views**                      | >70%              | ~0%             | 🟡 MEDIA   | Después de services            |
| `accounts.views`               | >75%              | ~0%             | 🟡 MEDIA   | Login, logout, profile         |
| `projects.views`               | >70%              | ~0%             | 🟡 MEDIA   | Dashboard, proyectos           |
| `orgs.views`                   | >75%              | ~0%             | 🟡 MEDIA   | Organizaciones                 |
| `files.views`                  | >75%              | ~0%             | 🟡 MEDIA   | Uploads/downloads              |
| **Middleware**                 | >85%              | ~0%             | 🔴 ALTA    | Afecta todas las requests      |
| `accounts.middleware`          | >85%              | ~0%             | 🔴 ALTA    | Authentication                 |
| `orgs.middleware`              | >85%              | ~0%             | 🔴 ALTA    | Organization context           |
| `plans.middleware`             | >85%              | ~0%             | 🔴 ALTA    | Subscription checks            |
| **Signals & Forms**            | >75%              | ~0%             | 🟡 MEDIA   | Después de models/services     |
| `accounts.signals`             | >80%              | ~0%             | 🟡 MEDIA   | 4 signals activos              |
| `orgs.signals`                 | >80%              | ~0%             | 🟡 MEDIA   | Cache invalidation             |
| `accounts.forms`               | >75%              | ~0%             | 🟢 BAJA    | Validaciones formularios       |

### Objetivos de Tests por Tipo

| Tipo de Test          | Objetivo | Actual | Completado | ETA       |
|-----------------------|----------|--------|------------|-----------|
| **Unit Tests**        | 150+     | 33     | 22%        | 2-3 sem   |
| Models                | 60       | 33     | 55%        | 1 semana  |
| Services              | 40       | 0      | 0%         | 1 semana  |
| Validators/Security   | 30       | 0      | 0%         | 3-4 días  |
| Views                 | 20       | 0      | 0%         | 3-4 días  |
| **Integration Tests** | 15+      | 0      | 0%         | 1 semana  |
| User Onboarding       | 4        | 0      | 0%         | 2 días    |
| Subscription Workflow | 4        | 0      | 0%         | 2 días    |
| Project Lifecycle     | 4        | 0      | 0%         | 2 días    |
| File Upload           | 3        | 0      | 0%         | 1 día     |
| **E2E Tests**         | 8+       | 0      | 0%         | 3-4 días  |
| **TOTAL**             | **173+** | **33** | **19%**    | **4-5 sem**|

### KPIs de Calidad

| KPI                           | Objetivo | Actual | Estado | Notas                               |
|-------------------------------|----------|--------|--------|-------------------------------------|
| **Coverage General**          | >80%     | ~26%   | 🔴     | Nominal 48%, real 26%               |
| **Coverage Crítico (Security)** | >95%   | ~0%    | 🔴     | files.security sin tests            |
| **Tests Pasando**             | 100%     | 100%   | ✅     | 33/33 tests User                    |
| **Tiempo Unit Tests**         | <2 min   | ~15s   | ✅     | Excelente performance               |
| **Flakiness**                 | <1%      | 0%     | ✅     | Sin tests intermitentes             |
| **Build Pass Rate**           | >95%     | N/A    | 🟡     | Sin CI/CD configurado               |
| **Reducción Bugs Prod**       | >70%     | N/A    | 🟡     | Medir después de 3 meses            |

### Objetivos de Funcionalidad Crítica

Cada funcionalidad crítica debe tener:

✅ **3+ tests mínimo** que cubran:
- 1 test de happy path
- 2+ tests de edge cases
- 1+ test de error handling

✅ **Logging validado** en:
- User create/update/delete → **INFO** (success), **WARNING** (duplicate), **ERROR** (validation)
- Subscription create/upgrade/cancel → **INFO** (success), **WARNING** (downgrade), **ERROR** (payment)
- File upload/download → **INFO** (success), **WARNING** (size limit), **ERROR** (invalid type)
- Transaction create/update → **INFO** (success), **WARNING** (low balance), **ERROR** (insufficient)

✅ **Security tests** para prevenir:
- File uploads maliciosos (path traversal, MIME spoofing, size bombs)
- Authentication bypass (session hijacking, credential stuffing)
- Authorization bypass (horizontal/vertical privilege escalation)
- SQL Injection (ORM misuse, raw queries)
- XSS (template injection, unsafe rendering)

✅ **Métricas de producción**:
- 0 bugs de seguridad críticos en 6 meses
- >70% reducción de bugs después de 3 meses con testing completo
- <5% rollback rate en deploys
- <10 min tiempo promedio de detección de bugs en CI/CD

---

## 🎯 PATTERNS Y BEST PRACTICES

### Patrón AAA (Arrange-Act-Assert)

Todos los tests deben seguir la estructura AAA para claridad:

```python
def test_user_can_update_profile(disable_account_signals):
    # ========================================
    # ARRANGE - Preparar datos y contexto
    # ========================================
    user = UserFactory(
        email="old@example.com",
        first_name="OldName"
    )
    new_email = "new@example.com"
    new_first_name = "NewName"
    
    # ========================================
    # ACT - Ejecutar la acción bajo test
    # ========================================
    user.email = new_email
    user.first_name = new_first_name
    user.save()
    
    # ========================================
    # ASSERT - Verificar resultados
    # ========================================
    user.refresh_from_db()
    assert user.email == new_email
    assert user.first_name == new_first_name
    # LOG ESPERADO: INFO - "User updated: user_id=123, email=new@example.com"
```

### Uso Correcto de Factories

**✅ BIEN - Factory para setup limpio:**
```python
def test_user_can_login(disable_account_signals):
    # Factory crea objeto válido sin signals
    user = UserFactory(email="test@example.com")
    user.set_password("password123")
    user.save()
    
    # Test real de login
    authenticated = user.check_password("password123")
    assert authenticated is True
```

**❌ MAL - Factory oculta validación que queremos probar:**
```python
def test_email_must_be_unique():
    # ❌ Factory usa get_or_create, NO lanza IntegrityError
    user1 = UserFactory(email="same@example.com")
    user2 = UserFactory(email="same@example.com")  # ❌ No falla!
    
    # ✅ CORRECTO - Usar create() directo
    user1 = User.objects.create_user(email="same@example.com", password="pass")
    with pytest.raises(IntegrityError):
        user2 = User.objects.create_user(email="same@example.com", password="pass")
```

### Cuándo Deshabilitar Signals

**✅ Unit Tests → Deshabilitar signals**
```python
@pytest.mark.unit
def test_user_model_default_values(disable_account_signals):
    """
    Unit test: Solo probamos el modelo, sin signals ni side effects.
    """
    user = UserFactory(email="test@example.com")
    assert user.is_active is True
    assert user.date_joined is not None
```

**✅ Integration Tests → Habilitar signals**
```python
@pytest.mark.integration
def test_user_creation_sets_names_from_email():  # SIN disable_account_signals
    """
    Integration test: Probamos que signal ensure_names_present funciona.
    """
    user = User.objects.create_user(
        email="john.doe@example.com",
        password="password123"
    )
    # Signal auto-llena nombres desde email
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    # LOG ESPERADO: INFO - "User names auto-filled from email"
```

### Naming Conventions

**Nombres de Tests Descriptivos:**
```python
# ✅ BIEN - Describe WHAT y WHY
def test_admin_cannot_delete_themselves()
def test_file_upload_rejects_executable_mime_types()
def test_subscription_downgrade_logs_warning()

# ❌ MAL - Demasiado genérico
def test_user()
def test_delete()
def test_upload()
```

**Nombres de Factories Consistentes:**
```python
# ✅ BIEN - Sufijo Factory, describe estado
UserFactory
SuperUserFactory
InactiveUserFactory
OrgAdminFactory

# ❌ MAL - Inconsistente
CreateUser
MakeUser
TestUserObject
```

### Fixtures Reutilizables

**✅ BIEN - Fixture por responsabilidad:**
```python
@pytest.fixture
def authenticated_client(db):
    """Cliente HTTP autenticado como usuario regular."""
    user = UserFactory()
    client = Client()
    client.force_login(user)
    return client

@pytest.fixture
def admin_client(db):
    """Cliente HTTP autenticado como superuser."""
    admin = SuperUserFactory()
    client = Client()
    client.force_login(admin)
    return client
```

**❌ MAL - Fixture hace demasiadas cosas:**
```python
@pytest.fixture
def setup_everything(db):
    """❌ Fixture monolítico difícil de mantener"""
    user = UserFactory()
    org = OrganizationFactory()
    plan = PlanFactory()
    subscription = SubscriptionFactory()
    project = ProjectFactory()
    # ... 20 líneas más
    return {"user": user, "org": org, ...}  # ❌ Dictionary hell
```

### Parametrize para Reducir Duplicación

**✅ BIEN - Un test, múltiples casos:**
```python
@pytest.mark.parametrize("email,is_valid", [
    ("valid@example.com", True),
    ("invalid.email", False),
    ("@nodomain.com", False),
    ("noemail@", False),
    ("", False),
])
def test_email_validation(email, is_valid):
    if is_valid:
        user = User.objects.create_user(email=email, password="pass")
        assert user.email == email
    else:
        with pytest.raises(ValidationError):
            User.objects.create_user(email=email, password="pass")
```

**❌ MAL - Tests repetitivos:**
```python
def test_valid_email():
    user = User.objects.create_user(email="valid@example.com", password="pass")
    assert user.email == "valid@example.com"

def test_invalid_email_no_at():
    with pytest.raises(ValidationError):
        User.objects.create_user(email="invalid.email", password="pass")

# ... 5 tests más casi idénticos ❌
```

### Logging en Tests

**✅ BIEN - Validar logs esperados:**
```python
import logging

def test_user_creation_logs_success(disable_account_signals, caplog):
    """Verificar que creación exitosa loguea INFO."""
    with caplog.at_level(logging.INFO):
        user = User.objects.create_user(
            email="test@example.com",
            password="password123"
        )
    
    # Verificar que se logueó el evento
    assert "User created" in caplog.text
    assert user.email in caplog.text
    assert "INFO" in caplog.text
```

**✅ BIEN - Validar WARNING logs:**
```python
def test_duplicate_email_logs_warning(caplog):
    """Intentar crear email duplicado debe loguear WARNING."""
    User.objects.create_user(email="dup@example.com", password="pass")
    
    with caplog.at_level(logging.WARNING):
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="dup@example.com", password="pass")
    
    assert "Duplicate email" in caplog.text or "WARNING" in caplog.text
```

### Mocking de Servicios Externos

**✅ BIEN - Mock S3 uploads:**
```python
from unittest.mock import patch, MagicMock

@patch('arc_manager.apps.orgs.storage_service.boto3.client')
def test_file_upload_success(mock_boto):
    """Mock S3 para evitar uploads reales."""
    # Mock del cliente S3
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    
    # Test de upload
    result = upload_to_s3(file_data, "test.pdf")
    
    # Verificar que se llamó al método correcto
    mock_s3.upload_fileobj.assert_called_once()
    assert result["success"] is True
    # LOG ESPERADO: INFO - "File uploaded: filename=test.pdf, size=1024"
```

**❌ MAL - Test depende de S3 real:**
```python
def test_file_upload():
    """❌ Hace upload REAL a S3 en cada test"""
    result = upload_to_s3(file_data, "test.pdf")
    assert result["success"] is True
    # ❌ Lento, costoso, puede fallar por red
```

### Edge Cases Prioritarios

Cada test debe cubrir:

1. **Happy Path** (1 test)
2. **Boundary Values** (2+ tests)
   - Valores mínimos/máximos
   - Límites de tamaño
   - Extremos de rangos
3. **Invalid Input** (2+ tests)
   - Datos vacíos
   - Formatos incorrectos
   - Tipos erróneos
4. **Error Conditions** (1+ test)
   - Excepciones esperadas
   - Comportamiento en fallas

**Ejemplo completo:**
```python
class TestFileUploadSecurity:
    """Suite completa de tests de seguridad para uploads."""
    
    # Happy Path
    def test_upload_valid_pdf(self):
        file = create_pdf_file("valid.pdf", size_mb=1)
        result = upload_file(file)
        assert result.success is True
        # LOG: INFO - "File uploaded: filename=valid.pdf"
    
    # Boundary - Tamaño máximo permitido
    def test_upload_max_size_allowed(self):
        file = create_pdf_file("max.pdf", size_mb=10)  # 10MB es max
        result = upload_file(file)
        assert result.success is True
        # LOG: INFO - "Large file uploaded: size=10MB"
    
    # Boundary - Excede tamaño máximo
    def test_upload_exceeds_max_size(self):
        file = create_pdf_file("huge.pdf", size_mb=11)  # >10MB
        with pytest.raises(ValidationError, match="File too large"):
            upload_file(file)
        # LOG: WARNING - "File rejected: size=11MB exceeds limit"
    
    # Invalid - MIME type malicioso
    def test_upload_rejects_executable_mime(self):
        file = create_file("virus.exe", mime="application/x-msdownload")
        with pytest.raises(ValidationError, match="Invalid file type"):
            upload_file(file)
        # LOG: ERROR - "Security: Executable file rejected"
    
    # Invalid - MIME spoofing
    def test_upload_detects_mime_spoofing(self):
        # Archivo .exe renombrado como .pdf
        file = create_exe_file_as_pdf("fake.pdf")
        with pytest.raises(ValidationError, match="MIME mismatch"):
            upload_file(file)
        # LOG: ERROR - "Security: MIME spoofing detected"
    
    # Error - Path traversal attack
    def test_upload_prevents_path_traversal(self):
        file = create_pdf_file("../../../etc/passwd", size_mb=1)
        with pytest.raises(ValidationError, match="Invalid filename"):
            upload_file(file)
        # LOG: ERROR - "Security: Path traversal attempt blocked"
```

---

## 📅 FASES DE IMPLEMENTACIÓN

### **FASE 1: Fundamentos (1-2 semanas)** ✅ COMPLETADO 50%

**Objetivo:** Infraestructura básica y tests de modelos críticos.

**Completado:**
- ✅ pytest configurado en Docker
- ✅ Fixtures básicos (`conftest.py`, `disable_account_signals`)
- ✅ Factories: `UserFactory`, `OrgAdminFactory`, `SuperUserFactory`, `InactiveUserFactory`
- ✅ 33/33 tests User model pasando (100%)
- ✅ Bug crítico de logging arreglado (`message` → `detail`)

**Pendiente:**
- [ ] Factories: `PlanFactory`, `SubscriptionFactory`, `ProjectFactory`, `FileUploadFactory`
- [ ] Tests: Organization model (20+ tests)
- [ ] Tests: Plan model (15+ tests)
- [ ] Tests: Project model (15+ tests)
- [ ] Coverage real >50% en models

**Entregables Fase 1:**
- ✅ 33 tests User pasando
- [ ] 60+ tests models pasando
- [ ] Coverage models >80%
- [ ] 0 flaky tests

---

### **FASE 2: Lógica de Negocio (1-2 semanas)**

**Objetivo:** Tests de services, validators, y security.

**Tareas:**
- [ ] `test_plans/test_services.py` - Subscription create/upgrade/cancel (20+ tests)
- [ ] `test_projects/test_services.py` - Transactions, balances (15+ tests)
- [ ] `test_files/test_security.py` - Path traversal, MIME validation (15+ tests)
- [ ] `test_files/test_validators.py` - File size, type, extension (12+ tests)
- [ ] `test_core/test_validators.py` - Generic validators (10+ tests)
- [ ] Mock S3/R2 uploads en `test_orgs/test_storage_service.py`

**Entregables Fase 2:**
- [ ] 70+ tests services/validators pasando
- [ ] Coverage security >95%
- [ ] Coverage services >85%
- [ ] 0 bugs de seguridad conocidos

---

### **FASE 3: Integration Tests (1 semana)**

**Objetivo:** Tests end-to-end de workflows críticos.

**Tareas:**
- [ ] `integration/test_user_onboarding.py` (4 tests)
  - Registro → Confirmación email → Login → Crear org
- [ ] `integration/test_subscription_workflow.py` (4 tests)
  - Create plan → Subscribe → Upgrade → Cancel
- [ ] `integration/test_project_lifecycle.py` (4 tests)
  - Create project → Add transaction → Check balance → Close
- [ ] `integration/test_file_upload_workflow.py` (3 tests)
  - Upload → Validate → Store S3 → Download

**Entregables Fase 3:**
- [ ] 15+ integration tests pasando
- [ ] Todos los workflows críticos cubiertos
- [ ] Signals validados en contexto real
- [ ] Logs de producción validados

---

### **FASE 4: Views y Middleware (3-5 días)**

**Objetivo:** Tests de endpoints y middleware.

**Tareas:**
- [ ] `test_accounts/test_views.py` - Login, logout, register, profile (15+ tests)
- [ ] `test_accounts/test_middleware.py` - Authentication middleware (8+ tests)
- [ ] `test_orgs/test_middleware.py` - Organization context (8+ tests)
- [ ] `test_plans/test_middleware.py` - Subscription checks (8+ tests)
- [ ] `test_projects/test_views.py` - Dashboard, projects (12+ tests)
- [ ] `test_files/test_views.py` - Upload/download endpoints (10+ tests)

**Entregables Fase 4:**
- [ ] 60+ tests views/middleware pasando
- [ ] Coverage views >70%
- [ ] Coverage middleware >85%
- [ ] Todos los endpoints críticos cubiertos

---

### **FASE 5: Signals, Forms, y Coverage Gaps (3-5 días)**

**Objetivo:** Completar coverage de componentes restantes.

**Tareas:**
- [ ] `test_accounts/test_signals.py` - 4 signals (12+ tests)
- [ ] `test_orgs/test_signals.py` - Cache invalidation (8+ tests)
- [ ] `test_files/test_storage_signals.py` - S3 cleanup (6+ tests)
- [ ] `test_accounts/test_forms.py` - User forms (10+ tests)
- [ ] `test_orgs/test_forms.py` - Org forms (8+ tests)
- [ ] Análisis de coverage gaps y tests adicionales

**Entregables Fase 5:**
- [ ] 44+ tests signals/forms pasando
- [ ] Coverage signals >80%
- [ ] Coverage forms >75%
- [ ] Coverage general >80%

---

### **FASE 6: CI/CD y Optimización (3-5 días)**

**Objetivo:** Automatización y performance.

**Tareas:**
- [ ] Configurar GitHub Actions CI/CD
  - [ ] Run tests en cada PR
  - [ ] Coverage report en cada PR
  - [ ] Branch protection con coverage mínimo 80%
- [ ] Optimizar tests lentos (target <2 min para unit tests)
- [ ] Configurar ejecución paralela (`pytest -n auto`)
- [ ] Smoke tests ampliados para producción
- [ ] Documentación final y onboarding

**Entregables Fase 6:**
- [ ] CI/CD funcionando
- [ ] Tests ejecutándose <2 min
- [ ] README con instrucciones completas
- [ ] 0 flaky tests
- [ ] Coverage report automatizado

---

## 📚 GLOSARIO

### Tipos de Tests

| Término | Definición | Ejemplo en este proyecto |
|---------|------------|--------------------------|
| **Unit Test** | Test de una unidad aislada (función, método, clase) sin dependencias externas. Usa mocks/stubs. | `test_user_creation_with_factory()` - Solo prueba creación de User, sin signals |
| **Integration Test** | Test de múltiples componentes trabajando juntos. Incluye BD, signals, cache. | `test_user_onboarding()` - Usuario registra, confirma email, crea org |
| **E2E Test** | Test de flujo completo desde UI hasta BD, simulando usuario real. | Login → Upload file → Download file → Logout |
| **Smoke Test** | Test rápido que verifica funcionalidad básica después de deploy. | `test_mvp_ready.py` - ¿App arranca? ¿BD conecta? |
| **Regression Test** | Test para verificar que bug arreglado no vuelva a aparecer. | Test para bug de logging `message` vs `detail` |
| **Flaky Test** | Test que a veces pasa y a veces falla sin cambios en código. | Tests con `time.sleep()`, random data sin seed |
| **Mutation Test** | Introduce bugs automáticamente para verificar que tests los detecten. | Cambiar `>` por `>=` y ver si tests fallan |

### Herramientas y Frameworks

| Herramienta | Propósito | Uso en este proyecto |
|-------------|-----------|---------------------|
| **pytest** | Framework de testing principal para Python | Ejecuta todos los tests, maneja fixtures, markers |
| **pytest-django** | Plugin de pytest para Django | Maneja BD de test, settings, fixtures Django |
| **factory_boy** | Librería para crear objetos de test realistas | `UserFactory`, `OrganizationFactory`, etc. |
| **faker** | Genera datos realistas (nombres, emails, direcciones) | Usado por factories para emails/nombres únicos |
| **pytest-cov** | Plugin de coverage para pytest | Genera reportes de cobertura HTML/terminal |
| **freezegun** | Congela tiempo para tests deterministas | Tests que dependen de `datetime.now()` |
| **responses** | Mock de requests HTTP | Mock APIs externas (payment gateways) |
| **pytest-xdist** | Ejecución paralela de tests | `pytest -n 4` para usar 4 CPUs |

### Conceptos Clave

| Concepto | Definición | Por qué importa |
|----------|------------|-----------------|
| **Coverage** | % de líneas de código ejecutadas por tests | Coverage 80% no significa 80% de bugs encontrados, pero ayuda |
| **Fixture** | Función que prepara datos/estado para tests | Evita duplicación, hace tests más limpios |
| **Mock** | Objeto falso que simula comportamiento real | Evita llamadas a S3, BD externa, APIs de pago |
| **Stub** | Mock que retorna valores predefinidos | `stub_s3_upload()` siempre retorna `success=True` |
| **Spy** | Mock que registra cómo fue llamado | Verificar que función se llamó con parámetros correctos |
| **Marker** | Etiqueta para categorizar tests | `@pytest.mark.unit`, `@pytest.mark.slow` |
| **Parametrize** | Ejecutar mismo test con diferentes inputs | Reduce duplicación, cubre más casos |
| **Arrange-Act-Assert (AAA)** | Patrón de estructura de tests | Setup → Ejecutar → Verificar |

### Estrategias de Testing

| Estrategia | Cuándo usar | Cuándo NO usar |
|------------|-------------|----------------|
| **Test Pyramid** | 70% Unit, 20% Integration, 10% E2E | Proyecto con UI compleja (invertir pirámide) |
| **TDD (Test-Driven Development)** | Funcionalidad nueva, bugs complejos | Prototipos rápidos, spikes |
| **BDD (Behavior-Driven Development)** | Features orientadas a usuario | Lógica puramente técnica |
| **Property-Based Testing** | Validaciones complejas, parsers | Tests simples de CRUD |
| **Mutation Testing** | Validar calidad de tests existentes | Proyecto sin tests base |

### Logs y Structured Logging

| Término | Definición | Ejemplo en este proyecto |
|---------|------------|--------------------------|
| **Structured Logging** | Logs en formato JSON con campos consistentes | `{"level": "INFO", "event": "user_created", "user_id": 123}` |
| **INFO** | Evento de negocio exitoso, normal operation | User created, File uploaded |
| **WARNING** | Comportamiento sospechoso pero no crítico | Duplicate email attempt, File size near limit |
| **ERROR** | Fallo que requiere atención, operación falló | Payment failed, File upload rejected |
| **CRITICAL** | Sistema no funciona, requiere acción inmediata | BD caída, S3 inaccesible |
| **Log Context** | Metadata adicional en logs (user_id, org_id) | Ayuda a rastrear bugs en producción |

---

## 📝 RESUMEN EJECUTIVO

### Estado Actual del Proyecto (4 Nov 2025 - Sesión 3)

**✅ Logros:**
- 33/33 tests User model pasando (100%)
- Infraestructura de testing completa (pytest + Docker)
- 4 factories creadas (User, SuperUser, OrgAdmin, InactiveUser)
- Bug crítico de logging encontrado y arreglado
- Estrategia de 3 capas definida (Unit 70% / Integration 20% / E2E 10%)
- Documentación exhaustiva creada:
  - `PLAN_TESTING_COMPLETO.md` - Estrategia y roadmap
  - `TESTS_DOCUMENTATION.md` - Análisis detallado de cada test

**🔴 Gaps Críticos:**
- Coverage real ~26% (nominal 48%, pero sin tests de integration/security)
- 0 tests de security (files.security sin coverage)
- 0 tests de integration (workflows sin probar)
- 0 tests de logging (logs no validados)
- 95+ tests faltantes identificados:
  - 25 edge cases (boundary values, invalid input)
  - 15 security tests (MIME, path traversal, XSS)
  - 12 integration tests (workflows end-to-end)
  - 10 logging tests (INFO/WARNING/ERROR validados)
  - 33+ tests para otros models (Org, Plan, Project, File)

**🎯 Prioridades Inmediatas (Próximas 2-3 semanas):**
1. **Security Tests** (CRÍTICO - 3-4 días)
   - `test_files/test_security.py` - Path traversal, MIME validation
   - `test_files/test_validators.py` - File size, type checks
2. **Models Restantes** (ALTO - 1 semana)
   - Organization, Plan, Project, File models
   - Edge cases y validaciones
3. **Integration Tests** (ALTO - 1 semana)
   - User onboarding workflow
   - Subscription lifecycle
   - File upload/download workflow

**📊 Métricas Clave:**
- Tests pasando: 33/33 (100%) ✅
- Coverage nominal: 48% 🟡
- Coverage real: ~26% 🔴
- Tests faltantes: 140+ 🔴
- Tiempo ejecución: <15s ✅

**🚀 Próximos Pasos:**
1. Crear `plan_factories.py` y `project_factories.py`
2. Implementar `test_files/test_security.py` (CRÍTICO)
3. Implementar tests de Organization model
4. Crear primer integration test (user onboarding)
5. Configurar CI/CD en GitHub Actions

---

**Documentación generada:** 4 Nov 2025  
**Última actualización:** Sesión 3 - Documentación completa  
**Próxima revisión:** Después de completar Fase 1 (60+ tests models)

---

## ✅ Checklist de Progreso

### Setup Inicial
- [x] Instalar pytest y dependencias ✅ (4 Nov 2025)
- [x] Crear `pytest.ini` ✅ (4 Nov 2025)
- [x] Crear `.coveragerc` ✅ (4 Nov 2025)
- [x] Crear `tests/conftest.py` ✅ (4 Nov 2025)
- [x] Actualizar `docker-compose.yml` con volúmenes ✅ (4 Nov 2025)
- [ ] Configurar GitHub Actions CI/CD
- [x] Ejecutar primer test exitoso ✅ (4 Nov 2025 - 2 tests pasando)

### Factories (Fase 1)
- [x] `account_factories.py` - UserFactory ✅ (4 Nov 2025)
  - [x] UserFactory
  - [x] SuperUserFactory
  - [x] OrgAdminFactory
  - [x] InactiveUserFactory
- [x] `org_factories.py` - OrganizationFactory ✅ (4 Nov 2025)
- [ ] `plan_factories.py` - PlanFactory, SubscriptionFactory
- [ ] `project_factories.py` - ProjectFactory, TransactionFactory
- [ ] `file_factories.py` - FileUploadFactory

### Unit Tests - Models (Fase 1)
- [🔄] `test_accounts/test_models.py` (En progreso - 2/33 tests pasando)
  - [x] Archivo creado con 33 tests
  - [x] 2 tests pasando
  - [ ] Arreglar 31 tests restantes
  - [ ] Alcanzar >80% coverage
- [ ] `test_orgs/test_models.py` (>80% coverage)
- [ ] `test_plans/test_models.py` (>80% coverage)
- [ ] `test_projects/test_models.py` (>80% coverage)
- [ ] `test_files/test_models.py` (>80% coverage)

### Unit Tests - Services (Fase 2)
- [ ] `test_plans/test_services.py` (>90% coverage)
- [ ] `test_projects/test_services.py` (>85% coverage)
- [ ] `test_orgs/test_storage_service.py` (>85% coverage)
- [ ] `test_projects/test_finance_cache.py` (>90% coverage)
- [ ] `test_orgs/test_cache_utils.py` (>80% coverage)

### Unit Tests - Security (Fase 3)
- [ ] `test_files/test_security.py` (100% coverage)
- [ ] `test_files/test_validators.py` (>90% coverage)
- [ ] `test_files/test_api.py` (>85% coverage)
- [ ] `test_core/test_validators.py` (>90% coverage)

### Unit Tests - Views (Fase 4)
- [ ] `test_accounts/test_views.py` (>75% coverage)
- [ ] `test_orgs/test_views.py` (>75% coverage)
- [ ] `test_projects/test_views.py` (>70% coverage)
- [ ] `test_files/test_views.py` (>75% coverage)
- [ ] `test_main/test_views.py` (>70% coverage)

### Unit Tests - Middleware (Fase 4)
- [ ] `test_accounts/test_middleware.py` (>85% coverage)
- [ ] `test_orgs/test_middleware.py` (>85% coverage)
- [ ] `test_plans/test_middleware.py` (>85% coverage)
- [ ] `test_core/test_middleware.py` (>85% coverage)

### Unit Tests - Signals & Forms (Fase 5)
- [ ] `test_accounts/test_signals.py` (>80% coverage)
- [ ] `test_orgs/test_signals.py` (>80% coverage)
- [ ] `test_files/test_storage_signals.py` (>80% coverage)
- [ ] `test_accounts/test_forms.py` (>75% coverage)
- [ ] `test_orgs/test_forms.py` (>75% coverage)
- [ ] `test_projects/test_forms.py` (>75% coverage)

### Integration Tests (Fase 5)
- [ ] `integration/test_user_onboarding.py`
- [ ] `integration/test_subscription_workflow.py`
- [ ] `integration/test_project_lifecycle.py`
- [ ] `integration/test_file_upload_workflow.py`

### Performance & Optimization (Fase 6)
- [ ] Optimizar tests lentos
- [ ] Implementar ejecución paralela
- [ ] `performance/test_query_performance.py`
- [ ] Smoke tests ampliados

### CI/CD
- [ ] GitHub Actions configurado
- [ ] Tests ejecutándose en cada PR
- [ ] Coverage report en cada PR
- [ ] Branch protection con coverage mínimo

### Documentación
- [ ] README actualizado con instrucciones de testing
- [ ] Guía de contribución con testing guidelines
- [ ] Ejemplos de tests en cada módulo

---

## 📝 Notas Adicionales

### Convenciones de Código

- Usar `pytest` fixtures en lugar de `setUp`/`tearDown` de unittest
- Preferir `factory_boy` sobre fixtures JSON
- Usar `freezegun` para tests que dependen de tiempo
- Usar `responses` o `requests-mock` para APIs externas
- Usar `@pytest.mark.django_db` solo cuando sea necesario
- Usar `@pytest.mark.parametrize` para reducir código duplicado

### Tests a Evitar

- ❌ Tests que dependen de servicios externos reales (S3, APIs de pago)
- ❌ Tests que dependen de orden de ejecución
- ❌ Tests con sleeps o waits (usar mocks de tiempo)
- ❌ Tests que modifican configuración global
- ❌ Tests que requieren internet

### Recursos Útiles

- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Django Testing Best Practices](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Python Testing with pytest (Book)](https://pragprog.com/titles/bopytest/)

---

## 🎯 Siguiente Sesión - Quick Start

Cuando retomes el trabajo en una nueva sesión, ejecuta estos comandos:

```bash
# 1. Verificar que Docker esté corriendo
docker-compose ps

# 2. Ver estado actual de tests
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/test_models.py -v --no-cov"

# 3. Ejecutar con coverage
docker-compose exec web bash -c "cd /app && python -m pytest tests/ --cov=arc_manager --cov-report=term-missing"

# 4. Listar todos los tests
docker-compose exec web bash -c "cd /app && python -m pytest --collect-only tests/"

# 5. Ver qué tests están fallando
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/test_models.py --lf -v"
```

### 📝 Notas de la Última Sesión (4 Nov 2025 - Sesión 2)

**Lo que se completó:**
- ✅ Arreglados TODOS los 33 tests del modelo User (100% passing!)
- ✅ Agregado fixture `disable_account_signals` para:
  - `validate_user_organization`
  - `validate_organization_limits`
  - `ensure_names_present`
  - `validate_admin_without_org`
- ✅ Corregido bug crítico en `structured_logging.py`:
  - Cambiado `data['message']` a `data['detail']` para evitar conflicto con LogRecord
- ✅ Mejorados tests para usar `User.objects.create_user()` directamente cuando necesario
- ✅ Ajustados tests para verificar comportamiento real vs esperado

**Bugs encontrados y arreglados:**
1. ✅ Logging KeyError - `'message'` conflicto con Python LogRecord
2. ✅ Signal `ensure_names_present` auto-llenando nombres desde email
3. ✅ Factory usando `django_get_or_create` evitando IntegrityError esperado
4. ✅ Método `can_manage_organization()` retornando None en vez de False

**Progreso de tests:**
- Sesión 1: 2/33 tests pasando (6%)
- Sesión 2: 33/33 tests pasando (100%) 🎉

**Archivos modificados:**
- `tests/unit/test_accounts/test_models.py` - Agregado `disable_account_signals` a 30+ tests
- `arc_manager/core/structured_logging.py` - Fix crítico de logging
- `tests/conftest.py` - Ampliado fixture para desconectar 4 signals

---

### 📝 Notas de Sesiones Anteriores

**Sesión 1 (4 Nov 2025):**

**Lo que funciona:**
- pytest ejecutándose en Docker ✅
- 2 tests pasando correctamente ✅
- Factories de User y Organization creadas ✅
- Sistema de fixtures funcionando ✅

**Lo que falta arreglar:**
- 31 tests que necesitan `disable_account_signals` ✅ COMPLETADO
- Error de logging en `test_email_is_required` ✅ COMPLETADO
- Crear factories de Plan, Subscription, Project, File

**Archivos clave creados:**
- `tests/conftest.py` - Fixtures globales
- `tests/factories/account_factories.py` - Factories de usuarios
- `tests/factories/org_factories.py` - Factory de organizaciones
- `tests/unit/test_accounts/test_models.py` - 33 tests del modelo User
- `pytest.ini` - Configuración de pytest
- `.coveragerc` - Configuración de coverage

**Comando más usado:**
```bash
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/test_models.py -v --no-cov"
```

---

**Fecha de Creación**: 4 de Noviembre, 2025  
**Última Actualización**: 4 de Noviembre, 2025 (Sesión 2 completada - ¡33/33 tests pasando!)  
**Autor**: Plan generado para ARC Manager Testing Strategy  
**Versión**: 1.2  
**Estado**: En progreso - Tests de User model completados al 100% ✅
