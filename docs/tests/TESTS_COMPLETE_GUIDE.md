# 🧪 GUÍA COMPLETA DE TESTS - ARC MANAGER

**Fecha:** 11 de Noviembre, 2025  
**Branch:** feat-orgs-unitests  
**Estado:** ~1120 tests | ~75% cobertura | 4/7 módulos completados

---

## 📊 ESTADO ACTUAL

### Tests Implementados por Módulo

| Módulo | Tests | Estado | Archivos |
|--------|-------|--------|----------|
| **ACCOUNTS** | 87 | ✅ 100% | Pre-existente |
| **ORGS** | ~385 | ✅ 90% | 6 archivos (models, admin, security, storage) |
| **PLANS** | ~378 | ✅ 100% | 7 archivos (models, admin, services, middleware) |
| **PROJECTS** | ~270 | ✅ 95% | 4 archivos + 17 factories |
| **FILES** | 0 | ⏳ 0% | **← SIGUIENTE (CRÍTICO)** |
| **USERS** | 0 | ⏳ 0% | Pendiente |
| **MAIN** | 0 | ⏳ 0% | Pendiente |

**Total:** ~1120 tests | **Cobertura:** ~75%

---

## 🎯 PRÓXIMO PASO: MÓDULO FILES

### ¿Por Qué es CRÍTICO?

- 🔒 **Seguridad:** Upload de archivos es vector de ataque común
- 💰 **Financiero:** Uso indebido de almacenamiento S3/R2  
- 📋 **Cumplimiento:** Validación de tipos y tamaños
- 🐛 **Bugs:** Validaciones insuficientes permiten exploits

### Archivos a Crear (en orden)

1. **`tests/factories/files/file_factories.py`**
   - FileFactory, ImageFileFactory, PDFFileFactory
   - MaliciousFileFactory (para security tests)

2. **`tests/files/security/test_file_security.py`** (~80 tests) **CRÍTICO**
   - Validación de tipos permitidos (whitelist)
   - Extensión vs MIME type matching
   - Prevención de ejecutables (.exe, .sh, .bat)
   - Path traversal (../, ..\)
   - Nombres maliciosos
   - Tamaño máximo
   - Control de acceso cross-org

3. **`tests/files/unit/test_file_models.py`** (~70 tests)
   - Creación, validaciones, relaciones
   - Propiedades y métodos
   - Edge cases

4. **`tests/files/unit/test_file_storage.py`** (~50 tests)
   - Cálculos de almacenamiento
   - Límites y validaciones
   - Integración con R2/S3 (mocked)

5. **`tests/files/admin/test_file_admin.py`** (~40 tests)
   - Admin interface tests

### Validaciones Críticas a Implementar

**Seguridad:**
- [ ] Extensión en whitelist
- [ ] MIME type coincide con extensión
- [ ] No es ejecutable
- [ ] Sin path traversal
- [ ] Sin caracteres especiales peligrosos
- [ ] Tamaño no excede límite
- [ ] Usuario tiene permisos de org

**Negocio:**
- [ ] Relacionado a proyecto válido
- [ ] Usuario tiene permisos sobre proyecto
- [ ] Organización tiene espacio disponible

**Edge Cases:**
- [ ] Nombre muy largo (>255 chars)
- [ ] Sin extensión
- [ ] Múltiples extensiones (.tar.gz)
- [ ] Extensión mayúsculas (.PDF)
- [ ] Unicode en nombre
- [ ] Tamaño 0 bytes
- [ ] Re-upload mismo archivo

---

## 📚 RESUMEN DE LO IMPLEMENTADO

### ACCOUNTS (87 tests) ✅
- Models, Views, Forms, Admin, Security, Middleware
- Bug encontrado y arreglado: Superusuarios limitados por org

### ORGS (~385 tests) ✅
- test_organization_models.py (~80 tests)
- test_client_models.py (~50 tests)
- test_storage_service.py (~45 tests)
- test_organization_admin.py (~70 tests)
- test_decorators.py (~80 tests)
- test_org_security.py (~60 tests)

### PLANS (~378 tests) ✅
- test_plan_models.py (~90 tests)
- test_subscription_models.py (~90 tests)
- test_payment_models.py (~60 tests)
- test_services.py (~40 tests)
- test_plan_admin.py (~50 tests)
- test_middleware.py (~40 tests)

### PROJECTS (~270 tests) ✅ RECIÉN COMPLETADO
- test_project_models.py (~90 tests)
  - Propiedades financieras (total_paid, remaining_amount, payment_percentage)
  - Propiedades de progreso (progress_percentage, contadores)
  - Custom Manager (with_payments, with_complete_data, etc)
  - Caché Redis (total_paid, progress_percentage)
  
- test_phase_models.py (~60 tests)
  - Estados (PENDING, IN_PROGRESS, COMPLETED)
  - Logging de cambios de estado
  - Relaciones CASCADE
  
- test_task_models.py (~75 tests)
  - Estados y prioridades
  - Save/delete con logging
  - Invalidación de caché
  - is_due_soon property
  
- test_payment_models.py (~45 tests)
  - percentage_of_total property
  - Integración financiera con Project
  - Invalidación de caché

**Factories:** 17 factories diferentes (Project, Phase, Task, Payment con variantes)

---

## 🐛 BUGS ENCONTRADOS

### Crítico (Arreglado)
✅ Superusuarios limitados por límite de organización (`apps/accounts/signals.py`)

### Potenciales (Documentados)
- ⚠️ No hay validación start_date < end_date (Project/Phase)
- ⚠️ Cliente puede ser de diferente organización (Project)
- ⚠️ Pagos pueden tener monto negativo/cero (ProjectPayment)
- ⚠️ Pagos pueden tener fechas futuras (ProjectPayment)
- ⚠️ No hay constraint de unicidad (project, order) en Phase

---

## 📋 ESTÁNDARES OBLIGATORIOS

### Estructura de Archivos

```python
"""
Tests exhaustivos para el modelo [ModelName]
Estos tests DEBEN detectar bugs reales.
"""
import pytest
from tests.factories import ...

@pytest.mark.django_db
@pytest.mark.unit
class Test[Model]Creation:
    """Tests de creación"""
    
@pytest.mark.django_db
@pytest.mark.unit
class Test[Model]Relationships:
    """Tests de relaciones"""
    
@pytest.mark.django_db  
@pytest.mark.unit
class Test[Model]Validations:
    """Tests de validaciones"""
    
@pytest.mark.django_db
@pytest.mark.unit
class Test[Model]EdgeCases:
    """Tests de edge cases"""
```

### Naming

✅ **Buenos nombres:**
- `test_file_cannot_have_executable_extension()`
- `test_user_cannot_access_file_from_different_org()`

❌ **Malos nombres:**
- `test_file_1()`
- `test_upload()`

### Comentarios

```python
def test_file_sanitization_removes_path_traversal(self):
    """
    SECURITY CRITICAL: Prevenir path traversal attacks
    
    BUG POTENCIAL: Si clean() no sanitiza, atacante podría
    escribir archivos fuera del directorio permitido.
    """
```

### Mocks

✅ **Mockear:** APIs externas, S3/R2, I/O, emails  
❌ **NO mockear:** Lógica de negocio, validaciones, queries DB

---

## 🔧 COMANDOS ÚTILES

```bash
# Ejecutar todos los tests
docker-compose exec web pytest tests/ -v

# Un módulo específico
docker-compose exec web pytest tests/projects/ -v

# Un archivo específico
docker-compose exec web pytest tests/projects/unit/test_project_models.py -v

# Un test específico
docker-compose exec web pytest tests/projects/unit/test_project_models.py::TestProjectCreation::test_creation_with_factory -v

# Con cobertura
docker-compose exec web pytest --cov=apps.projects --cov-report=html

# Solo security tests
docker-compose exec web pytest -m security -v

# Con output visible (debug)
docker-compose exec web pytest tests/files/ -v -s
```

---

## 📁 REFERENCIAS IMPORTANTES

### Para Entender el Código

```
arc_manager/apps/files/
  ├── models.py     # ← LEER PRIMERO para FILES
  ├── admin.py
  ├── forms.py
  └── views.py
```

### Ejemplos de Tests

**Mejor ejemplo de modelos:**
- `tests/projects/unit/test_project_models.py`
- Propiedades complejas, custom managers, edge cases

**Mejor ejemplo de security:**
- `tests/orgs/security/test_org_security.py`
- Control de acceso, prevención de ataques

**Mejor ejemplo de factories:**
- `tests/factories/projects/project_factories.py`
- 17 factories con variantes por estado

**Configuración:**
- `tests/projects/conftest.py`
- Deshabilitar signals, fixtures útiles

---

## 🎯 TEMPLATE DE FACTORY PARA FILES

```python
"""
Factories para modelos de Files
"""
import factory
from factory.django import DjangoModelFactory
from django.core.files.uploadedfile import SimpleUploadedFile

class FileFactory(DjangoModelFactory):
    class Meta:
        model = 'files.ProjectFile'
    
    project = factory.SubFactory('tests.factories.ProjectFactory')
    organization = factory.SubFactory('tests.factories.OrganizationFactory')
    uploaded_by = factory.SubFactory('tests.factories.UserFactory')
    
    name = factory.Sequence(lambda n: f'file_{n}.pdf')
    file_type = 'document'
    file_size = 1024
    mime_type = 'application/pdf'
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            obj.name,
            b"PDF content",
            content_type=obj.mime_type
        )
    )

class ImageFileFactory(FileFactory):
    name = factory.Sequence(lambda n: f'image_{n}.jpg')
    file_type = 'image'
    mime_type = 'image/jpeg'

class MaliciousFileFactory(FileFactory):
    name = '../../../etc/passwd'  # Path traversal
    file_type = 'unknown'
    mime_type = 'text/plain'
```

---

## ✅ CHECKLIST PARA COMPLETAR FILES

- [ ] Crear `tests/factories/files/file_factories.py`
- [ ] Actualizar `tests/factories/__init__.py`
- [ ] Crear `tests/files/conftest.py` con fixtures
- [ ] Implementar `test_file_security.py` (80 tests)
- [ ] Implementar `test_file_models.py` (70 tests)
- [ ] Implementar `test_file_storage.py` (50 tests)
- [ ] Implementar `test_file_admin.py` (40 tests)
- [ ] Ejecutar tests y verificar que pasen
- [ ] Actualizar este documento

---

## 🚀 PROMPT PARA CONTINUAR

Usa esto en una nueva sesión:

```
Continúa con la implementación de tests para ARC Manager.

ESTADO ACTUAL:
- ~1120 tests implementados (ACCOUNTS, ORGS, PLANS, PROJECTS)
- Cobertura: ~75%
- Próximo módulo: FILES (0% completado)

OBJETIVO:
Implementar el módulo FILES que es CRÍTICO por seguridad de uploads.

ORDEN DE IMPLEMENTACIÓN:
1. Factories (FileFactory, ImageFileFactory, MaliciousFileFactory)
2. Security Tests (~80 tests) - MÁS CRÍTICO
   - Validación tipos, extensiones, MIME types
   - Path traversal, ejecutables, control de acceso
3. Model Tests (~70 tests)
4. Storage Tests (~50 tests)  
5. Admin Tests (~40 tests)

REFERENCIAS:
- Lee: arc_manager/apps/files/models.py
- Ejemplos: tests/projects/unit/ (recién implementado)
- Security: tests/orgs/security/test_org_security.py
- Factories: tests/factories/projects/project_factories.py

ESTÁNDARES:
- Sigue patrones de tests/projects/
- NO tests superficiales - busca bugs reales
- Incluye edge cases y security tests
- Usa comentarios para bugs potenciales
- Nombres descriptivos

¿Listo para empezar con FILES?
```

---

## 📊 ESTRUCTURA DEL PROYECTO

```
arc_manager/
├── docs/
│   ├── tests/
│   │   └── TESTS_COMPLETE_GUIDE.md  ← Este archivo
│   ├── logging/       # Docs de logging
│   ├── security/      # Docs de seguridad
│   └── features/      # Docs de features
│
└── tests/
    ├── README.md
    ├── conftest.py
    ├── pytest.ini
    ├── factories/
    │   ├── accounts/
    │   ├── orgs/
    │   ├── plans/
    │   ├── projects/  ✅ NUEVO
    │   └── files/     ⏳ SIGUIENTE
    ├── accounts/      ✅ 87 tests
    ├── orgs/          ✅ ~385 tests
    ├── plans/         ✅ ~378 tests
    ├── projects/      ✅ ~270 tests
    ├── files/         ⏳ SIGUIENTE
    ├── users/         ⏳ Pendiente
    └── main/          ⏳ Pendiente
```

---

**Última actualización:** 11 de Noviembre, 2025  
**Próximo módulo:** FILES (CRÍTICO - Seguridad)  
**Progreso:** 4/7 módulos (57%)  
**Tests totales:** ~1120  
**Cobertura:** ~75%

