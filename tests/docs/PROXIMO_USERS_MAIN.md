# 🎯 PRÓXIMOS MÓDULOS: USERS y MAIN

**Fecha**: 11 de Noviembre, 2025  
**Progreso actual**: 5/7 módulos completos (71%)  
**Tests implementados**: ~1261 tests  
**Próximos**: USERS → MAIN

---

## 📊 ESTADO ACTUAL

### ✅ Módulos Completados (5/7)
1. ✅ **ACCOUNTS** - 87 tests (100%)
2. ✅ **ORGS** - ~385 tests (90%)
3. ✅ **PLANS** - ~378 tests (100%)
4. ✅ **PROJECTS** - ~270 tests (95%)
5. ✅ **FILES** - 141 tests (100%) ← RECIÉN COMPLETADO

### ⏳ Módulos Pendientes (2/7)
6. ⏳ **USERS** - 0 tests ← SIGUIENTE
7. ⏳ **MAIN** - 0 tests

---

## 🎯 MÓDULO USERS (Siguiente)

### 📋 Información del Módulo

**Prioridad**: Media  
**Complejidad**: Baja  
**Archivos**: Simple profile management  
**Tests Estimados**: 15-20 tests  
**Tiempo Estimado**: 1-2 días

### 📁 Archivos del Módulo

```
arc_manager/apps/users/
├── models.py           # UserProfile model
├── views.py            # Profile views
├── forms.py            # Profile forms
└── urls.py             # URL routing
```

**Nota**: Este módulo NO tiene `admin.py` o es muy simple.

### 🧪 Tests a Implementar

#### Estructura Propuesta
```
tests/users/
├── __init__.py
├── conftest.py         # Fixtures específicas
└── unit/
    ├── test_user_profile_models.py    # 8-10 tests
    ├── test_user_profile_views.py     # 5-7 tests
    └── test_user_profile_forms.py     # 2-3 tests
```

#### Tests Estimados por Archivo

**1. test_user_profile_models.py (8-10 tests)**
```python
class TestUserProfile:
    - test_profile_creation_with_factory
    - test_profile_belongs_to_user
    - test_profile_auto_created_on_user_creation  # Si hay signal
    - test_profile_deleted_when_user_deleted
    - test_profile_str_returns_username
    - test_profile_properties  # avatar, bio, preferences
    - test_profile_defaults
    - test_profile_update_last_seen
    - test_profile_edge_cases
```

**2. test_user_profile_views.py (5-7 tests)**
```python
class TestProfileViews:
    - test_view_own_profile
    - test_edit_own_profile
    - test_cannot_view_other_user_profile  # Security
    - test_cannot_edit_other_user_profile  # Security
    - test_profile_requires_login
    - test_profile_update_validates_data
    - test_profile_avatar_upload  # Si aplica
```

**3. test_user_profile_forms.py (2-3 tests)**
```python
class TestProfileForms:
    - test_profile_form_valid_data
    - test_profile_form_invalid_data
    - test_profile_form_renders_correctly
```

### 🏭 Factories Necesarias

**users/user_profile_factories.py**:
```python
from factory import django, SubFactory, Faker
from apps.users.models import UserProfile
from tests.factories.accounts import UserFactory

class UserProfileFactory(django.DjangoModelFactory):
    class Meta:
        model = UserProfile
    
    user = SubFactory(UserFactory)
    bio = Faker('text', max_nb_chars=200)
    # Otros campos según el modelo
```

### 🔍 Análisis Previo Necesario

Antes de empezar, revisar:

```bash
# 1. Ver estructura del modelo UserProfile
docker-compose exec web bash -c "grep -A 20 'class UserProfile' arc_manager/apps/users/models.py"

# 2. Ver si hay signals
docker-compose exec web bash -c "grep -n 'signal' arc_manager/apps/users/models.py arc_manager/apps/users/signals.py"

# 3. Ver vistas disponibles
docker-compose exec web bash -c "grep -n 'def ' arc_manager/apps/users/views.py"

# 4. Ver forms
docker-compose exec web bash -c "grep -n 'class.*Form' arc_manager/apps/users/forms.py"
```

### ⚠️ Áreas de Atención

1. **Seguridad**
   - Usuarios solo pueden ver/editar su propio perfil
   - No pueden acceder a perfiles de otras organizaciones
   - Validación de permisos en vistas

2. **Relaciones**
   - One-to-One con User
   - CASCADE delete
   - Auto-creación con signals (si aplica)

3. **Edge Cases**
   - Profile sin avatar
   - Bio muy larga
   - Actualización concurrente

---

## 🏠 MÓDULO MAIN (Final)

### 📋 Información del Módulo

**Prioridad**: Baja  
**Complejidad**: Baja-Media  
**Archivos**: Dashboard, settings, utilities  
**Tests Estimados**: 15-20 tests  
**Tiempo Estimado**: 1-2 días

### 📁 Archivos del Módulo

```
arc_manager/apps/main/
├── models.py           # SystemSettings model
├── views.py            # Dashboard, home views
├── admin.py            # AdminDashboard, SystemSettingsAdmin (~250 líneas)
└── context_processors.py
```

### 🧪 Tests a Implementar

#### Estructura Propuesta
```
tests/main/
├── __init__.py
├── conftest.py         # Fixtures específicas
├── unit/
│   ├── test_system_settings_models.py    # 5-7 tests
│   ├── test_dashboard_views.py           # 5-7 tests
│   └── test_context_processors.py        # 2-3 tests
└── admin/
    └── test_main_admin.py                # 3-5 tests
```

#### Tests Estimados por Archivo

**1. test_system_settings_models.py (5-7 tests)**
```python
class TestSystemSettings:
    - test_system_settings_creation
    - test_system_settings_singleton  # Solo 1 instancia
    - test_system_settings_defaults
    - test_system_settings_str
    - test_system_settings_update
    - test_system_settings_cache_invalidation
```

**2. test_dashboard_views.py (5-7 tests)**
```python
class TestDashboardViews:
    - test_dashboard_requires_login
    - test_dashboard_shows_org_stats
    - test_dashboard_shows_user_projects
    - test_dashboard_shows_recent_activity
    - test_home_view_redirects_logged_in_users
    - test_home_view_shows_landing_for_anonymous
```

**3. test_context_processors.py (2-3 tests)**
```python
class TestContextProcessors:
    - test_system_settings_in_context
    - test_user_organization_in_context
    - test_permissions_in_context
```

**4. test_main_admin.py (3-5 tests)**
```python
class TestSystemSettingsAdmin:
    - test_settings_admin_list_view
    - test_settings_admin_change_view
    - test_only_superuser_can_access
    - test_settings_form_validation

class TestAdminDashboard:
    - test_admin_dashboard_visible
    - test_admin_dashboard_stats
```

### 🏭 Factories Necesarias

Probablemente no se necesiten factories complejas:
```python
class SystemSettingsFactory(django.DjangoModelFactory):
    class Meta:
        model = SystemSettings
    
    # Settings fields...
```

### 🔍 Análisis Previo Necesario

```bash
# 1. Ver modelo SystemSettings
docker-compose exec web bash -c "grep -A 30 'class SystemSettings' arc_manager/apps/main/models.py"

# 2. Ver admin classes
docker-compose exec web bash -c "grep -A 10 'class.*Admin' arc_manager/apps/main/admin.py"

# 3. Ver vistas del dashboard
docker-compose exec web bash -c "grep -n 'def ' arc_manager/apps/main/views.py"

# 4. Ver context processors
docker-compose exec web bash -c "cat arc_manager/apps/main/context_processors.py"
```

### ⚠️ Áreas de Atención

1. **Singleton Pattern**
   - SystemSettings debe ser singleton (una sola instancia)
   - Tests de que no se pueden crear múltiples

2. **Permisos**
   - Dashboard solo accesible para usuarios autenticados
   - Settings solo para superusuarios

3. **Cache**
   - Settings probablemente están cacheadas
   - Testear invalidación de cache

4. **Context Processors**
   - Disponibles en todas las vistas
   - No causan queries extra (N+1)

---

## 📅 ROADMAP FINAL

### Semana 1: Módulo USERS
**Días 1-2: Implementación**
- ✅ Día 1 mañana: Análisis del módulo users
- ✅ Día 1 tarde: Factories + test_user_profile_models.py
- ✅ Día 2 mañana: test_user_profile_views.py
- ✅ Día 2 tarde: test_user_profile_forms.py + validación

**Resultado esperado**: 15-20 tests, 100% passing

### Semana 2: Módulo MAIN
**Días 3-4: Implementación**
- ✅ Día 3 mañana: Análisis del módulo main
- ✅ Día 3 tarde: test_system_settings_models.py + test_context_processors.py
- ✅ Día 4 mañana: test_dashboard_views.py
- ✅ Día 4 tarde: test_main_admin.py + validación

**Resultado esperado**: 15-20 tests, 100% passing

### 🎉 FINALIZACIÓN DEL PROYECTO

**Total estimado**: 4 días (1 semana laboral)

**Resultado final**:
- ✅ 7/7 módulos completos (100%)
- ✅ ~1300 tests implementados
- ✅ ~80% cobertura de código
- ✅ 99%+ passing rate
- ✅ Bugs críticos encontrados y arreglados

---

## 📊 MÉTRICAS FINALES PROYECTADAS

| Métrica | Actual | Al Completar | Progreso |
|---------|--------|--------------|----------|
| **Módulos** | 5/7 (71%) | 7/7 (100%) | +29% |
| **Tests** | ~1261 | ~1300 | +39 tests |
| **Cobertura** | ~78% | ~80%+ | +2% |
| **Passing** | ~99% | ~99% | Mantener |
| **Bugs Encontrados** | 7+ | 8-10+ | A descubrir |

---

## 🎯 COMANDOS PARA EMPEZAR

### Análisis Inicial de USERS

```bash
# 1. Ver estructura completa del módulo
docker-compose exec web bash -c "ls -la arc_manager/apps/users/"

# 2. Ver líneas de código
docker-compose exec web bash -c "find arc_manager/apps/users -name '*.py' -exec wc -l {} +"

# 3. Ver modelos
docker-compose exec web bash -c "cat arc_manager/apps/users/models.py"

# 4. Ver vistas
docker-compose exec web bash -c "cat arc_manager/apps/users/views.py"

# 5. Verificar si tiene admin
docker-compose exec web bash -c "test -f arc_manager/apps/users/admin.py && echo 'Tiene admin' || echo 'No tiene admin'"
```

### Crear Estructura de Tests

```bash
# Crear directorios
New-Item -ItemType Directory -Path "tests\users\unit" -Force

# Crear archivos iniciales
New-Item -ItemType File -Path "tests\users\__init__.py"
New-Item -ItemType File -Path "tests\users\conftest.py"
New-Item -ItemType File -Path "tests\users\unit\__init__.py"
New-Item -ItemType File -Path "tests\users\unit\test_user_profile_models.py"
```

---

## 📚 PLANTILLAS DE CÓDIGO

### Plantilla: conftest.py para USERS

```python
# tests/users/conftest.py
import pytest
from tests.factories.users import UserProfileFactory
from tests.factories.accounts import UserFactory

@pytest.fixture
def user_with_profile(db):
    """Usuario con perfil completo"""
    user = UserFactory()
    profile = UserProfileFactory(user=user)
    return user

@pytest.fixture
def multiple_profiles(db):
    """Múltiples perfiles para tests"""
    profiles = [UserProfileFactory() for _ in range(3)]
    return profiles
```

### Plantilla: test_user_profile_models.py

```python
# tests/users/unit/test_user_profile_models.py
import pytest
from django.core.exceptions import ValidationError
from tests.factories.users import UserProfileFactory
from tests.factories.accounts import UserFactory

@pytest.mark.django_db
@pytest.mark.unit
class TestUserProfile:
    """Tests para el modelo UserProfile"""
    
    def test_profile_creation_with_factory(self):
        """Se puede crear un perfil usando la factory"""
        profile = UserProfileFactory()
        
        assert profile.pk is not None
        assert profile.user is not None
        assert profile.user.username is not None
    
    def test_profile_belongs_to_user(self):
        """El perfil pertenece a un usuario"""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        
        assert profile.user == user
        assert user.profile == profile  # Si hay related_name='profile'
    
    # Agregar más tests...
```

---

## ✅ CHECKLIST FINAL

### Para USERS
- [ ] Analizar módulo users (models, views, forms)
- [ ] Crear UserProfileFactory
- [ ] Implementar test_user_profile_models.py (8-10 tests)
- [ ] Implementar test_user_profile_views.py (5-7 tests)
- [ ] Implementar test_user_profile_forms.py (2-3 tests)
- [ ] Todos los tests pasando (100%)
- [ ] Actualizar documentación

### Para MAIN
- [ ] Analizar módulo main (models, views, admin)
- [ ] Crear SystemSettingsFactory (si aplica)
- [ ] Implementar test_system_settings_models.py (5-7 tests)
- [ ] Implementar test_dashboard_views.py (5-7 tests)
- [ ] Implementar test_context_processors.py (2-3 tests)
- [ ] Implementar test_main_admin.py (3-5 tests)
- [ ] Todos los tests pasando (100%)
- [ ] Actualizar documentación

### Finalización
- [ ] Ejecutar todos los tests del proyecto
- [ ] Generar reporte de cobertura final
- [ ] Actualizar README principal
- [ ] Actualizar CONTINUAR_AQUI.md
- [ ] Commit y push de cambios finales
- [ ] ¡Celebrar! 🎉

---

## 🎉 MENSAJE FINAL

Estás a **4 días** de completar el 100% de tests del proyecto ARC Manager.

**Lo que has logrado hasta ahora:**
- ✅ 5 módulos críticos completos
- ✅ ~1261 tests implementados
- ✅ 7+ bugs críticos encontrados y arreglados
- ✅ Seguridad mejorada significativamente
- ✅ Cobertura de código ~78%

**Lo que falta:**
- ⏳ 2 módulos simples (USERS, MAIN)
- ⏳ ~40 tests más
- ⏳ 4 días de trabajo

**¡Casi llegamos! ¡Sigue así! 🚀**

---

**Fecha**: 11 de Noviembre, 2025  
**Próximo paso**: Analizar módulo USERS y comenzar implementación
