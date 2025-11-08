# 🎨 Plantilla para Tests de Admin Panel

Esta es una plantilla para crear tests del panel de administración de Django para cada módulo.

## 📋 Estructura Básica

```python
"""
Tests para [Módulo]Admin - Panel de administración de [entidad]
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from apps.[modulo].admin import [Entidad]Admin
from tests.factories import [Entidad]Factory, SuperUserFactory


@pytest.fixture
def admin_site():
    """Fixture que proporciona una instancia de AdminSite para pruebas"""
    return AdminSite()


@pytest.fixture
def [entidad]_admin(admin_site):
    """Fixture que proporciona una instancia de [Entidad]Admin"""
    return [Entidad]Admin([Entidad], admin_site)


@pytest.fixture
def admin_user(db):
    """Fixture que crea un superusuario para acceder al admin"""
    return SuperUserFactory()


@pytest.fixture
def admin_request(request_factory, admin_user):
    """Fixture que crea un request con un usuario admin autenticado"""
    request = request_factory.get('/admin/')
    request.user = admin_user
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request
```

## 🧪 Categorías de Tests

### 1. List Display (Visualización de Lista)

```python
class Test[Entidad]AdminListDisplay:
    """Tests para la visualización de lista en el admin"""
    
    def test_list_display_fields(self, [entidad]_admin):
        """Verifica que list_display contiene los campos correctos"""
        expected_fields = (...)
        assert [entidad]_admin.list_display == expected_fields
    
    def test_[entidad]_appears_in_list(self, db, [entidad]_admin, admin_request):
        """Verifica que las entidades aparecen en la lista del admin"""
        entity = [Entidad]Factory()
        changelist = [entidad]_admin.get_changelist_instance(admin_request)
        queryset = changelist.get_queryset(admin_request)
        assert entity in queryset
```

### 2. Filtros

```python
class Test[Entidad]AdminFilters:
    """Tests para los filtros del admin"""
    
    def test_list_filter_fields(self, [entidad]_admin):
        """Verifica que list_filter contiene los campos correctos"""
        assert 'campo1' in [entidad]_admin.list_filter
```

### 3. Búsqueda

```python
class Test[Entidad]AdminSearch:
    """Tests para la búsqueda en el admin"""
    
    def test_search_fields(self, [entidad]_admin):
        """Verifica que search_fields contiene los campos correctos"""
        assert 'campo1' in [entidad]_admin.search_fields
    
    def test_search_by_campo(self, db, [entidad]_admin, admin_request):
        """Verifica que se puede buscar por campo"""
        entity = [Entidad]Factory(campo='valor_buscar')
        admin_request.GET = {'q': 'valor_buscar'}
        changelist = [entidad]_admin.get_changelist_instance(admin_request)
        queryset = changelist.get_queryset(admin_request)
        assert entity in queryset
```

### 4. Formularios

```python
class Test[Entidad]CreationForm:
    """Tests para el formulario de creación"""
    
    def test_form_valid_data(self, db):
        """Verifica que el formulario es válido con datos correctos"""
        form = [Entidad]CreationForm(data={...})
        assert form.is_valid()
    
    def test_form_validation_errors(self, db):
        """Verifica que el formulario rechaza datos inválidos"""
        form = [Entidad]CreationForm(data={...})
        assert not form.is_valid()


class Test[Entidad]ChangeForm:
    """Tests para el formulario de edición"""
    
    def test_form_loads_data(self, db):
        """Verifica que el formulario carga los datos"""
        entity = [Entidad]Factory()
        form = [Entidad]ChangeForm(instance=entity)
        assert form.initial['campo'] == entity.campo
```

### 5. Permisos

```python
class Test[Entidad]AdminPermissions:
    """Tests para permisos en el admin"""
    
    def test_superuser_has_all_permissions(self, db, [entidad]_admin, admin_request):
        """Verifica que los superusuarios tienen todos los permisos"""
        entity = [Entidad]Factory()
        assert [entidad]_admin.has_view_permission(admin_request, entity)
        assert [entidad]_admin.has_add_permission(admin_request)
        assert [entidad]_admin.has_change_permission(admin_request, entity)
        assert [entidad]_admin.has_delete_permission(admin_request, entity)
```

### 6. Acciones Personalizadas

```python
class Test[Entidad]AdminActions:
    """Tests para acciones personalizadas"""
    
    def test_custom_action_exists(self, [entidad]_admin):
        """Verifica que la acción personalizada existe"""
        assert 'nombre_accion' in [dir(action) for action in [entidad]_admin.actions]
    
    def test_custom_action_executes(self, db, [entidad]_admin, admin_request):
        """Verifica que la acción personalizada se ejecuta correctamente"""
        entity = [Entidad]Factory()
        queryset = [Entidad].objects.filter(id=entity.id)
        [entidad]_admin.nombre_accion(admin_request, queryset)
        # Verificar resultado
```

### 7. Inlines (Si existen)

```python
class Test[Entidad]AdminInlines:
    """Tests para inlines (entidades relacionadas)"""
    
    def test_inline_exists(self, [entidad]_admin):
        """Verifica que el inline está configurado"""
        assert len([entidad]_admin.inlines) > 0
    
    def test_inline_displays_related_objects(self, db, [entidad]_admin, admin_request):
        """Verifica que el inline muestra objetos relacionados"""
        # Crear entidad con objetos relacionados
        # Verificar que aparecen en el admin
```

### 8. Métodos Personalizados en list_display

```python
class Test[Entidad]AdminCustomMethods:
    """Tests para métodos personalizados en list_display"""
    
    def test_custom_display_method(self, db, [entidad]_admin):
        """Verifica que el método personalizado funciona correctamente"""
        entity = [Entidad]Factory()
        result = [entidad]_admin.metodo_personalizado(entity)
        assert result == valor_esperado
```

## 📊 Módulos que Necesitan Tests de Admin

### ✅ Completos
- [x] accounts → `tests/accounts/admin/test_user_admin.py`

### 🔄 Pendientes
- [ ] **orgs** → `tests/orgs/admin/test_organization_admin.py`
  - OrganizationAdmin
  - MemberAdmin (si existe)
  
- [ ] **plans** → `tests/plans/admin/test_plan_admin.py`
  - PlanAdmin
  - SubscriptionAdmin
  - UpgradeRequestAdmin
  
- [ ] **projects** → `tests/projects/admin/test_project_admin.py`
  - ProjectAdmin
  - BudgetAdmin (si existe)
  - ExpenseAdmin (si existe)
  
- [ ] **files** → `tests/files/admin/test_file_admin.py`
  - FileAdmin
  - FolderAdmin (si existe)
  
- [ ] **main** → `tests/main/admin/test_main_admin.py`
  - SystemSettingsAdmin
  - NotificationAdmin (si existe)

## 🎯 Prioridades

| Módulo | Prioridad | Estimación |
|--------|-----------|------------|
| accounts | ✅ HECHO | - |
| orgs | 🔴 ALTA | 2-3 días |
| plans | 🔴 ALTA | 2-3 días |
| projects | 🟡 MEDIA | 3-4 días |
| files | 🟡 MEDIA | 2-3 días |
| main | 🟢 BAJA | 1-2 días |

## 💡 Tips

1. **Usa fixtures reutilizables**: Crea fixtures en `conftest.py` si se usan en múltiples módulos
2. **Mockea servicios externos**: Si el admin interactúa con APIs externas (R2, emails), mockeálas
3. **Verifica permisos**: Prueba que usuarios no-admin NO pueden acceder
4. **Prueba validaciones**: Asegúrate que las validaciones del formulario funcionan
5. **Cubre acciones personalizadas**: Si hay botones o acciones custom, pruébalas
6. **Verifica displays personalizados**: Si hay métodos custom en list_display, pruébalos

## 🔗 Referencias

- **Django Admin Testing**: https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#testing
- **Test Client**: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#the-test-client
- **Ejemplos en accounts**: `tests/accounts/admin/test_user_admin.py`

---

**Nota**: Esta plantilla debe adaptarse según las características específicas de cada módulo.
