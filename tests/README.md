# 🧪 ARC Manager - Test Suite Documentation

**Última actualización**: 4 de Noviembre, 2025  
**Framework**: pytest 8.4.2 + pytest-django + Factory Boy  
**Python**: 3.11.13 | Django: 5.2

---

## 📊 Estado General

| Métrica | Valor |
|---------|-------|
| **Tests Totales** | 60 tests (46 unit + 14 integration) |
| **Unit Tests** | ✅ 46 pasando, 1 skipped |
| **Integration Tests** | ✅ 14 pasando (CON signals activos) |
| **Coverage Funcional** | 67% (60/89 funcionalidades) |
| **Último Run** | ✅ 100% success rate |
| **Ambiente** | Docker Compose (PostgreSQL) |

⚠️ **CRÍTICO**: Los 46 unit tests usan `disable_account_signals` (lógica aislada). Los 14 integration tests prueban comportamiento REAL de producción con signals activos.

---

## 🗂️ Estructura de Tests

```
tests/
├── conftest.py                          # Fixtures globales y configuración
├── factories/                           # Factory Boy - datos de prueba
│   ├── account_factories.py            # UserFactory
│   └── org_factories.py                # OrganizationFactory
├── unit/test_accounts/                  # Tests unitarios (signals DESACTIVADOS)
│   ├── test_user_models.py             # 33 tests: manager, campos, métodos
│   ├── test_user_logging.py            # 3 tests: eventos de negocio (GDPR/SOX)
│   ├── test_user_unicode.py            # 2 tests: 10 idiomas internacionales
│   ├── test_user_validation.py         # 4 tests: límites RFC 5321, normalización
│   └── test_user_relationships.py      # 1 test: CASCADE delete Organization
├── integration/test_accounts/           # ⭐ NUEVO - Tests de integración
│   └── test_user_signals.py            # 14 tests: signals activos (PRODUCCIÓN)
└── security/test_accounts/              # Tests de seguridad
    └── test_user_security.py            # 3 tests: timing attacks, password logging

📄 DOCUMENTACIÓN:
├── README.md                           # Este archivo
├── CONTINUAR_AQUI.md                   # ⭐ Estado actual + próximos pasos
├── AUDITORIA_MODELO_USER.md            # Matriz 89 funcionalidades
└── PLAN_TESTING_COMPLETO.md            # Roadmap fases 0-5
```

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
# Ejecutar TODOS los tests (unit + integration + security)
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/ tests/integration/test_accounts/ tests/security/test_accounts/ -v --no-cov"

# Ejecutar solo tests de integración (signals activos - PRODUCCIÓN)
docker-compose exec web bash -c "cd /app && python -m pytest tests/integration/test_accounts/ -v --tb=short"

# Ejecutar solo tests unitarios (signals desactivados - lógica aislada)
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/ -v"

# Ejecutar solo tests de seguridad
docker-compose exec web bash -c "cd /app && python -m pytest tests/security/test_accounts/ -v"

# Ejecutar test específico
docker-compose exec web bash -c "cd /app && python -m pytest tests/integration/test_accounts/test_user_signals.py::TestSignalEnsureNamesPresent::test_generates_names_from_email_with_dot -v"

# Ver solo tests fallidos (útil para debugging)
docker-compose exec web bash -c "cd /app && python -m pytest tests/ --lf -v"

# Coverage detallado
docker-compose exec web bash -c "cd /app && python -m pytest tests/unit/test_accounts/ --cov=apps.accounts --cov-report=term-missing"
```

---

## 📦 Tests Implementados

### 🔵 UNIT TESTS (Lógica Aislada - 46 tests)

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

### 🟢 INTEGRATION TESTS (Comportamiento Real - 14 tests) ⭐ NUEVO

**NO usan** `disable_account_signals` → Signals ACTIVOS como en producción.

#### `test_user_signals.py` - Signals en Producción (14 tests)

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
| **Unit Tests** | 46 | ✅ | Desactivados |
| **Integration Tests** | 14 | ✅ | Activos |
| **Security Tests** | 3 | ✅ | Desactivados |
| **Total** | **60** | ✅ | Mixto |

**Coverage Real**: 67% de 89 funcionalidades identificadas

---

## 📚 Documentación Relacionada

### Empezar Aquí
👉 **`CONTINUAR_AQUI.md`** - Estado actual + próximos pasos

### Referencia Completa
- **`AUDITORIA_MODELO_USER.md`** - Matriz 89 funcionalidades
- **`PLAN_TESTING_COMPLETO.md`** - Roadmap fases 0-5

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

## 📈 Progreso por Fase

| Fase | Tests | Estado | Coverage |
|------|-------|--------|----------|
| **Fase 0** | 33 tests | ✅ Completa | Base funcional |
| **Fase 1** | 3 tests | ✅ Completa | Seguridad crítica |
| **Fase 2** | 10 tests | ✅ Completa | Logging + Unicode + Validación |
| **Fase 2.5** | 14 tests | ✅ Completa | Integration tests (signals) |
| **Fase 3** | ~10 tests | ⏳ Pendiente | Save() + Org methods |
| **Fase 4** | ~10 tests | ⏸️ Futura | Middleware + Edge cases |
| **Fase 5** | ~10 tests | ⏸️ Futura | Performance + Integración completa |

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
