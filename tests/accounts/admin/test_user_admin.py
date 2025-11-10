"""
Tests para UserAdmin - Panel de administración de usuarios

Prueba las funcionalidades del panel admin de Django para el modelo User:
- Lista de usuarios (list_display)
- Filtros (list_filter)
- Búsqueda (search_fields)
- Formularios de creación y edición
- Acciones personalizadas
- Permisos y acceso
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from apps.accounts.admin import UserAdmin, UserCreationForm, UserChangeForm
from tests.factories import UserFactory, SuperUserFactory, OrganizationFactory

User = get_user_model()


@pytest.fixture
def admin_site():
    """Fixture que proporciona una instancia de AdminSite para pruebas"""
    return AdminSite()


@pytest.fixture
def user_admin(admin_site):
    """Fixture que proporciona una instancia de UserAdmin"""
    return UserAdmin(User, admin_site)


@pytest.fixture
def admin_user(db):
    """Fixture que crea un superusuario para acceder al admin"""
    return SuperUserFactory(
        email='admin@test.com',
        first_name='Admin',
        last_name='Test'
    )


@pytest.fixture
def request_factory():
    """Fixture que proporciona un RequestFactory"""
    return RequestFactory()


@pytest.fixture
def admin_request(request_factory, admin_user):
    """Fixture que crea un request con un usuario admin autenticado"""
    request = request_factory.get('/admin/')
    request.user = admin_user
    # Agregar messages para simular el comportamiento del admin
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request


class TestUserAdminListDisplay:
    """Tests para la visualización de lista en el admin"""
    
    def test_list_display_fields(self, user_admin):
        """Verifica que list_display contiene los campos correctos"""
        expected_fields = (
            'email', 
            'email_status_display', 
            'full_name', 
            'get_organization_link', 
            'get_role_display', 
            'is_active', 
            'date_joined'
        )
        assert user_admin.list_display == expected_fields
    
    def test_user_appears_in_list(self, db, user_admin, admin_request, disable_account_signals):
        """Verifica que los usuarios aparecen en la lista del admin"""
        user = UserFactory(email='testuser@example.com')
        
        changelist = user_admin.get_changelist_instance(admin_request)
        queryset = changelist.get_queryset(admin_request)
        
        assert user in queryset
    
    def test_full_name_display(self, db, user_admin, disable_account_signals):
        """Verifica que full_name se muestra correctamente"""
        user = UserFactory(first_name='John', last_name='Doe')
        
        full_name = user_admin.full_name(user)
        
        assert full_name == 'John Doe'


class TestUserAdminFilters:
    """Tests para los filtros del admin"""
    
    def test_list_filter_fields(self, user_admin):
        """Verifica que list_filter contiene los campos correctos"""
        assert 'is_active' in user_admin.list_filter
        assert 'is_staff' in user_admin.list_filter
        assert 'is_org_admin' in user_admin.list_filter
        # El admin usa organization__name para filtrar por nombre de org
        assert 'organization__name' in user_admin.list_filter


class TestUserAdminSearch:
    """Tests para la búsqueda en el admin"""
    
    def test_search_fields(self, user_admin):
        """Verifica que search_fields contiene los campos correctos"""
        assert 'email' in user_admin.search_fields
        assert 'first_name' in user_admin.search_fields
        assert 'last_name' in user_admin.search_fields
    
    def test_search_by_email(self, db, user_admin, admin_request, disable_account_signals):
        """Verifica que se puede buscar por email"""
        from django.http import QueryDict
        
        user = UserFactory(email='searchme@example.com')
        UserFactory(email='other@example.com')
        
        # GET debe ser un QueryDict, no un dict normal
        query_dict = QueryDict(mutable=True)
        query_dict['q'] = 'searchme'
        admin_request.GET = query_dict
        
        changelist = user_admin.get_changelist_instance(admin_request)
        queryset = changelist.get_queryset(admin_request)
        
        assert user in queryset
        assert queryset.count() == 1


class TestUserCreationForm:
    """Tests para el formulario de creación de usuarios"""
    
    def test_form_valid_data(self, db, disable_account_signals):
        """Verifica que el formulario es válido con datos correctos"""
        org = OrganizationFactory()
        form = UserCreationForm(data={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'organization': org.id,
        })
        
        assert form.is_valid(), f"Form errors: {form.errors}"
    
    def test_form_duplicate_email(self, db, disable_account_signals):
        """Verifica que el formulario rechaza emails duplicados"""
        UserFactory(email='duplicate@example.com')
        
        form = UserCreationForm(data={
            'email': 'duplicate@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_form_generates_password(self, db, disable_account_signals):
        """Verifica que el formulario genera una contraseña automáticamente"""
        org = OrganizationFactory()
        form = UserCreationForm(data={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'organization': org.id,
        })
        
        assert form.is_valid()
        user = form.save()
        
        # Verificar que tiene contraseña hasheada
        assert user.password
        assert user.password.startswith('pbkdf2_sha256$')
        # Verificar que se requiere cambio de contraseña
        assert user.password_change_required is True


class TestUserChangeForm:
    """Tests para el formulario de edición de usuarios"""
    
    def test_form_loads_user_data(self, db, disable_account_signals):
        """Verifica que el formulario carga los datos del usuario"""
        user = UserFactory()
        
        form = UserChangeForm(instance=user)
        
        assert form.initial['email'] == user.email
        assert form.initial['first_name'] == user.first_name
        assert form.initial['last_name'] == user.last_name
    
    def test_form_updates_user(self, db, disable_account_signals):
        """Verifica que el formulario actualiza los datos del usuario"""
        user = UserFactory(first_name='Old')
        
        form = UserChangeForm(
            data={
                'email': user.email,
                'first_name': 'New',
                'last_name': user.last_name,
                'password': user.password,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_org_admin': user.is_org_admin,
                'password_change_required': user.password_change_required,
                'organization': user.organization.id if user.organization else '',
            },
            instance=user
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        updated_user = form.save()
        
        assert updated_user.first_name == 'New'


class TestUserAdminPermissions:
    """Tests para permisos en el admin"""
    
    def test_superuser_has_all_permissions(self, db, user_admin, admin_request, disable_account_signals):
        """Verifica que los superusuarios tienen todos los permisos"""
        # Usamos disable_account_signals para evitar validación de límites
        user = UserFactory()
        
        assert user_admin.has_view_permission(admin_request, user)
        assert user_admin.has_add_permission(admin_request)
        assert user_admin.has_change_permission(admin_request, user)
        assert user_admin.has_delete_permission(admin_request, user)


# TODO: Agregar más tests para:
# - Acciones personalizadas (custom actions)
# - Inlines si existen
# - Métodos personalizados en list_display
# - Export/Import funcionalidad
# - Validaciones especiales
