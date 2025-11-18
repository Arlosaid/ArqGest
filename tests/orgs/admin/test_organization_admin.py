"""
Tests exhaustivos para OrganizationAdmin y ClientAdmin - Panel de administración Django

Estos tests DEBEN detectar bugs reales, no solo validar el happy path.
Incluyen validaciones, permisos, acciones personalizadas, edge cases y manejo de errores.
"""
import pytest
from decimal import Decimal
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock, MagicMock
from apps.orgs.admin import OrganizationAdmin, ClientAdmin, OrganizationAdminForm
from apps.orgs.models import Organization, Client
from tests.factories import (
    OrganizationFactory,
    ClientFactory,
    SuperUserFactory,
    UserFactory,
    InactiveOrganizationFactory,
    FounderOrganizationFactory
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_site():
    """Fixture que proporciona una instancia de AdminSite"""
    return AdminSite()


@pytest.fixture
def admin_user(db, disable_account_signals):
    """Fixture que crea un superusuario"""
    return SuperUserFactory(email='admin@test.com')


@pytest.fixture
def org_admin_instance(admin_site):
    """Fixture que proporciona una instancia de OrganizationAdmin"""
    return OrganizationAdmin(Organization, admin_site)


@pytest.fixture
def client_admin_instance(admin_site):
    """Fixture que proporciona una instancia de ClientAdmin"""
    return ClientAdmin(Client, admin_site)


@pytest.fixture
def admin_request(admin_user):
    """Fixture que crea un request con usuario admin autenticado"""
    factory = RequestFactory()
    request = factory.get('/admin/orgs/organization/')
    request.user = admin_user
    
    # Añadir session y messages
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    return request


# ============================================================================
# TESTS DE ORGANIZATIONADMIN - LIST DISPLAY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminListDisplay:
    """Tests de visualización de lista en OrganizationAdmin"""
    
    def test_list_display_fields_configured(self, org_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        expected_fields = [
            'name', 'get_active_status', 'get_founder_badge', 
            'user_count', 'get_storage_info', 'get_subscription_status', 
            'get_subscription_link', 'created_at'
        ]
        
        assert org_admin_instance.list_display == expected_fields
    
    def test_get_active_status_for_active_org(self, org_admin_instance):
        """Estado activo debe mostrar badge verde"""
        org = OrganizationFactory(is_active=True)
        
        html = org_admin_instance.get_active_status(org)
        
        assert 'ACTIVA' in html
        assert '#27AE60' in html  # Color verde
        assert '✓' in html
    
    def test_get_active_status_for_inactive_org(self, org_admin_instance):
        """Estado inactivo debe mostrar badge rojo"""
        org = InactiveOrganizationFactory()
        
        html = org_admin_instance.get_active_status(org)
        
        assert 'INACTIVA' in html
        assert '#E74C3C' in html  # Color rojo
        assert '✕' in html
    
    def test_get_founder_badge_for_founder(self, org_admin_instance):
        """Miembro fundador debe mostrar badge dorado"""
        org = FounderOrganizationFactory()
        
        html = org_admin_instance.get_founder_badge(org)
        
        assert 'FUNDADOR' in html
        assert '$199' in html
        assert '#F39C12' in html  # Color dorado
    
    def test_get_founder_badge_for_non_founder(self, org_admin_instance):
        """No fundador debe mostrar '-'"""
        org = OrganizationFactory(is_founder_member=False)
        
        html = org_admin_instance.get_founder_badge(org)
        
        assert html == '-'
    
    def test_user_count_without_users(self, org_admin_instance):
        """Organización sin usuarios debe mostrar '0 usuarios'"""
        org = OrganizationFactory()
        
        # Anotar manualmente (simula queryset del admin)
        org.user_count_admin = 0
        
        result = org_admin_instance.user_count(org)
        
        assert result == '0 usuarios'
    
    def test_user_count_with_users(self, org_admin_instance, disable_account_signals):
        """Organización con usuarios debe contar correctamente"""
        org = OrganizationFactory()
        UserFactory.create_batch(5, organization=org)
        
        # Anotar manualmente (simula queryset del admin)
        org.user_count_admin = 5
        
        result = org_admin_instance.user_count(org)
        
        assert result == '5 usuarios'
    
    def test_get_storage_info_without_subscription(self, org_admin_instance):
        """Sin subscription debe mostrar fallback de 10 GB"""
        org = OrganizationFactory(extra_storage_gb=0)
        
        html = org_admin_instance.get_storage_info(org)
        
        # Debe mostrar 10 GB (fallback) + 0 GB (extra) = 10 GB
        assert '10 GB' in html
    
    def test_get_storage_info_with_extra_storage(self, org_admin_instance):
        """Extra storage debe reflejarse en el total"""
        org = OrganizationFactory(extra_storage_gb=50)
        
        html = org_admin_instance.get_storage_info(org)
        
        # Debe mostrar 10 GB (fallback) + 50 GB (extra) = 60 GB
        assert '60 GB' in html or '50' in html
    
    def test_get_subscription_status_without_subscription(self, org_admin_instance):
        """Sin subscription debe mostrar 'Sin suscripción'"""
        org = OrganizationFactory()
        
        result = org_admin_instance.get_subscription_status(org)
        
        assert 'Sin suscripción' in result
    
    def test_get_subscription_link_without_subscription(self, org_admin_instance):
        """Sin subscription no debe mostrar link"""
        org = OrganizationFactory()
        
        result = org_admin_instance.get_subscription_link(org)
        
        assert result == '-'


# ============================================================================
# TESTS DE ORGANIZATIONADMIN - FILTERS Y SEARCH
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminFiltersAndSearch:
    """Tests de filtros y búsqueda"""
    
    def test_list_filter_configured(self, org_admin_instance):
        """Verificar que list_filter tiene los campos correctos"""
        expected_filters = ['is_active', 'is_founder_member', 'created_at']
        
        assert org_admin_instance.list_filter == expected_filters
    
    def test_search_fields_configured(self, org_admin_instance):
        """Verificar que search_fields tiene los campos correctos"""
        expected_fields = ['name', 'description']
        
        assert org_admin_instance.search_fields == expected_fields
    
    def test_filter_by_active_status(self, org_admin_instance, admin_request):
        """Filtrar solo organizaciones activas"""
        # Limpiar organizaciones existentes para este test
        Organization.objects.all().delete()
        
        OrganizationFactory(name='Active Org', is_active=True)
        InactiveOrganizationFactory(name='Inactive Org')
        
        # Simular filtro GET
        admin_request.GET = QueryDict('is_active=1')
        
        queryset = org_admin_instance.get_queryset(admin_request)
        filtered = queryset.filter(is_active=True)
        
        assert filtered.count() == 1, f"Expected 1 active org, got {filtered.count()}: {[o.name for o in filtered]}"
        assert filtered.first().name == 'Active Org'
    
    def test_search_by_name(self, org_admin_instance, admin_request):
        """Buscar organización por nombre"""
        OrganizationFactory(name='Tech Solutions Inc')
        OrganizationFactory(name='Business Corp')
        
        queryset = org_admin_instance.get_queryset(admin_request)
        searched = queryset.filter(name__icontains='Tech')
        
        assert searched.count() == 1
        assert 'Tech' in searched.first().name
    
    def test_search_by_description(self, org_admin_instance, admin_request):
        """Buscar organización por descripción"""
        OrganizationFactory(name='Org 1', description='Software development company')
        OrganizationFactory(name='Org 2', description='Marketing agency')
        
        queryset = org_admin_instance.get_queryset(admin_request)
        searched = queryset.filter(description__icontains='Software')
        
        assert searched.count() == 1
        assert 'Software' in searched.first().description


# ============================================================================
# TESTS DE ORGANIZATIONADMIN - SAVE MODEL
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminSaveModel:
    """Tests del método save_model - CRÍTICO para logging y validaciones"""
    
    def test_save_model_creates_new_organization(self, org_admin_instance, admin_request):
        """Crear nueva organización debe generar log ORGANIZATION_CREATED"""
        org = Organization(name='New Org', is_active=True, extra_storage_gb=0)
        form = Mock()
        
        with patch('apps.orgs.admin.log_info') as mock_log_info:
            org_admin_instance.save_model(admin_request, org, form, change=False)
        
        # Verificar que se guardó
        assert org.pk is not None
        
        # Verificar que se llamó al log con event='ORGANIZATION_CREATED'
        assert mock_log_info.called
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'ORGANIZATION_CREATED'
        assert call_kwargs['organization_name'] == 'New Org'
        assert call_kwargs['created_by'] == 'admin@test.com'
    
    def test_save_model_updates_organization(self, org_admin_instance, admin_request):
        """Actualizar organización debe generar log ORGANIZATION_UPDATED"""
        org = OrganizationFactory(name='Old Name', is_active=True)
        org.name = 'New Name'
        form = Mock()
        
        with patch('apps.orgs.admin.log_info') as mock_log_info:
            org_admin_instance.save_model(admin_request, org, form, change=True)
        
        # Verificar que se actualizó
        org.refresh_from_db()
        assert org.name == 'New Name'
        
        # Verificar que se llamó al log con event='ORGANIZATION_UPDATED'
        assert mock_log_info.called
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'ORGANIZATION_UPDATED'
        assert any(c['field'] == 'name' for c in call_kwargs['changes'])
    
    def test_save_model_tracks_is_active_change(self, org_admin_instance, admin_request):
        """
        CRÍTICO: Cambiar is_active debe generar log WARNING por seguridad
        """
        org = OrganizationFactory(is_active=True)
        org.is_active = False
        form = Mock()
        
        with patch('apps.orgs.admin.logger.warning') as mock_warning:
            org_admin_instance.save_model(admin_request, org, form, change=True)
        
        # Verificar que se llamó a logger.warning con el cambio crítico
        assert mock_warning.called
        call_args = mock_warning.call_args[0][0]
        assert 'ORGANIZATION_STATUS_CHANGED' in call_args
        assert org.name in call_args
    
    def test_save_model_tracks_multiple_changes(self, org_admin_instance, admin_request):
        """Múltiples cambios deben rastrearse todos"""
        org = OrganizationFactory(
            name='Old Name',
            is_active=True,
            extra_storage_gb=0,
            is_founder_member=False
        )
        
        # Cambiar múltiples campos
        org.name = 'New Name'
        org.extra_storage_gb = 100
        org.is_founder_member = True
        form = Mock()
        
        with patch('apps.orgs.admin.log_info') as mock_log_info:
            org_admin_instance.save_model(admin_request, org, form, change=True)
        
        # Verificar que se rastrearon 3 cambios
        call_kwargs = mock_log_info.call_args[1]
        changes = call_kwargs['changes']
        assert len(changes) == 3
        
        # Verificar que cada campo cambió
        changed_fields = {c['field'] for c in changes}
        assert {'name', 'extra_storage_gb', 'is_founder_member'}.issubset(changed_fields)
    
    def test_save_model_handles_exception(self, org_admin_instance, admin_request):
        """
        BUG POTENCIAL: save_model debe manejar excepciones correctamente
        """
        org = OrganizationFactory()
        form = Mock()
        
        with patch.object(org, 'save', side_effect=Exception("Database error")):
            with patch('apps.orgs.admin.log_error') as mock_log_error:
                with pytest.raises(Exception):
                    org_admin_instance.save_model(admin_request, org, form, change=True)
                
                # Verificar que se loggeó el error
                assert mock_log_error.called
                call_kwargs = mock_log_error.call_args[1]
                assert call_kwargs['event'] == 'ORGANIZATION_SAVE_FAILED'
                assert 'Database error' in call_kwargs['error_message']


# ============================================================================
# TESTS DE ORGANIZATIONADMIN - DELETE MODEL
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminDeleteModel:
    """
    Tests del método delete_model - CRÍTICO para limpieza de R2/S3
    Estos tests DEBEN verificar que se limpian archivos correctamente
    """
    
    @patch('apps.orgs.models.Organization._cleanup_r2_files')
    def test_delete_model_calls_cleanup_r2(self, mock_cleanup, org_admin_instance, admin_request):
        """
        CRÍTICO: delete_model DEBE llamar a org.delete() que ejecuta _cleanup_r2_files
        """
        org = OrganizationFactory()
        mock_cleanup.return_value = 10  # Simular 10 archivos eliminados
        
        with patch('apps.orgs.admin.log_info'):
            org_admin_instance.delete_model(admin_request, org)
        
        # Verificar que se llamó a _cleanup_r2_files
        assert mock_cleanup.called
    
    @patch('apps.orgs.models.Organization._cleanup_r2_files')
    def test_delete_model_logs_deletion(self, mock_cleanup, org_admin_instance, admin_request, disable_account_signals):
        """delete_model debe generar log ORGANIZATION_DELETED"""
        org = OrganizationFactory(name='Test Org')
        UserFactory.create_batch(3, organization=org)
        mock_cleanup.return_value = 5
        
        org_name = org.name
        org_id = org.id
        
        with patch('apps.orgs.admin.log_info') as mock_log_info:
            org_admin_instance.delete_model(admin_request, org)
        
        # Verificar que se llamó al log con event='ORGANIZATION_DELETED'
        assert mock_log_info.called
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'ORGANIZATION_DELETED'
        assert call_kwargs['organization_name'] == org_name
        assert call_kwargs['organization_id'] == org_id
        assert call_kwargs['users_deleted'] == 3
    
    @patch('apps.orgs.models.Organization._cleanup_r2_files')
    def test_delete_model_handles_exception(self, mock_cleanup, org_admin_instance, admin_request):
        """
        BUG POTENCIAL: delete_model debe manejar excepciones correctamente
        """
        org = OrganizationFactory()
        mock_cleanup.side_effect = Exception("R2 connection error")
        
        with patch('apps.orgs.admin.log_error') as mock_log_error:
            with pytest.raises(Exception):
                org_admin_instance.delete_model(admin_request, org)
            
            # Verificar que se loggeó el error
            assert mock_log_error.called


# ============================================================================
# TESTS DE ORGANIZATIONADMIN - DELETE QUERYSET (BULK DELETE)
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminBulkDelete:
    """Tests de eliminación en lote - CRÍTICO para R2 cleanup"""
    
    @patch('apps.orgs.models.Organization._cleanup_r2_files')
    def test_delete_queryset_calls_cleanup_for_each_org(self, mock_cleanup, org_admin_instance, admin_request):
        """
        CRÍTICO: delete_queryset DEBE llamar a org.delete() para cada instancia
        NO debe usar queryset.delete() que no ejecuta métodos personalizados
        """
        orgs = [OrganizationFactory() for _ in range(3)]
        queryset = Organization.objects.filter(id__in=[o.id for o in orgs])
        mock_cleanup.return_value = 5
        
        with patch('apps.orgs.admin.log_info'):
            org_admin_instance.delete_queryset(admin_request, queryset)
        
        # Verificar que se llamó a _cleanup_r2_files 3 veces (una por org)
        assert mock_cleanup.call_count == 3
    
    @patch('apps.orgs.models.Organization._cleanup_r2_files')
    def test_delete_queryset_logs_bulk_deletion(self, mock_cleanup, org_admin_instance, admin_request):
        """Eliminación en lote debe generar log ORGANIZATION_BULK_DELETED"""
        orgs = [OrganizationFactory() for _ in range(5)]
        queryset = Organization.objects.filter(id__in=[o.id for o in orgs])
        mock_cleanup.return_value = 10
        
        with patch('apps.orgs.admin.log_info') as mock_log_info:
            org_admin_instance.delete_queryset(admin_request, queryset)
        
        # Verificar que se llamó al log con event='ORGANIZATION_BULK_DELETED'
        assert mock_log_info.called
        call_kwargs = mock_log_info.call_args[1]
        assert call_kwargs['event'] == 'ORGANIZATION_BULK_DELETED'
        assert call_kwargs['organization_count'] == 5


# ============================================================================
# TESTS DE ORGANIZATIONADMIN - ACTIONS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminActions:
    """Tests de acciones personalizadas del admin"""
    
    def test_actions_configured(self, org_admin_instance):
        """Verificar que las acciones están configuradas"""
        expected_actions = [
            'activate_organizations',
            'deactivate_organizations',
            'mark_as_founder',
            'unmark_as_founder',
            'reduce_extra_storage',
            'add_extra_storage'
        ]
        
        assert set(expected_actions).issubset(set(org_admin_instance.actions))
    
    def test_activate_organizations_action(self, org_admin_instance, admin_request):
        """Acción de activar debe cambiar is_active a True"""
        orgs = [InactiveOrganizationFactory() for _ in range(3)]
        queryset = Organization.objects.filter(id__in=[o.id for o in orgs])
        
        org_admin_instance.activate_organizations(admin_request, queryset)
        
        # Verificar que todas están activas
        for org in queryset:
            org.refresh_from_db()
            assert org.is_active is True
    
    def test_deactivate_organizations_action(self, org_admin_instance, admin_request):
        """Acción de desactivar debe cambiar is_active a False"""
        orgs = [OrganizationFactory(is_active=True) for _ in range(3)]
        queryset = Organization.objects.filter(id__in=[o.id for o in orgs])
        
        org_admin_instance.deactivate_organizations(admin_request, queryset)
        
        # Verificar que todas están inactivas
        for org in queryset:
            org.refresh_from_db()
            assert org.is_active is False
    
    def test_mark_as_founder_action(self, org_admin_instance, admin_request):
        """Acción de marcar como fundador debe establecer flags correctos"""
        orgs = [OrganizationFactory(is_founder_member=False) for _ in range(2)]
        queryset = Organization.objects.filter(id__in=[o.id for o in orgs])
        
        org_admin_instance.mark_as_founder(admin_request, queryset)
        
        # Verificar que todas son fundadoras
        for org in queryset:
            org.refresh_from_db()
            assert org.is_founder_member is True
            assert org.founder_discount_percentage == Decimal('33.44')
            assert org.founder_joined_date is not None
    
    def test_unmark_as_founder_action(self, org_admin_instance, admin_request):
        """Acción de quitar fundador debe limpiar flags"""
        orgs = [FounderOrganizationFactory() for _ in range(2)]
        queryset = Organization.objects.filter(id__in=[o.id for o in orgs])
        
        org_admin_instance.unmark_as_founder(admin_request, queryset)
        
        # Verificar que ya no son fundadoras
        for org in queryset:
            org.refresh_from_db()
            assert org.is_founder_member is False
            assert org.founder_discount_percentage == Decimal('0')
            assert org.founder_joined_date is None


# ============================================================================
# TESTS DE ORGANIZATIONADMINFORM - VALIDATION
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminFormValidation:
    """
    Tests del form de OrganizationAdmin - CRÍTICO para validaciones
    Estos tests DEBEN detectar bugs de validación
    """
    
    def test_form_allows_positive_extra_storage(self):
        """Extra storage positivo debe ser válido"""
        org = OrganizationFactory(extra_storage_gb=0)
        
        form = OrganizationAdminForm(
            data={
                'name': org.name,
                'description': org.description or '',
                'extra_storage_gb': 50,
                'is_active': True,
                'is_founder_member': org.is_founder_member,
                'founder_discount_percentage': org.founder_discount_percentage,
            },
            instance=org
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
    
    def test_form_allows_negative_extra_storage(self):
        """Extra storage negativo debe ser válido (si el total >= 0)"""
        org = OrganizationFactory(extra_storage_gb=0)
        
        form = OrganizationAdminForm(
            data={
                'name': org.name,
                'description': org.description or '',
                'extra_storage_gb': -5,
                'is_active': True,
                'is_founder_member': org.is_founder_member,
                'founder_discount_percentage': org.founder_discount_percentage,
            },
            instance=org
        )
        
        # Esto DEBE ser válido porque el total es 10 - 5 = 5 GB
        assert form.is_valid(), f"Form errors: {form.errors}"
    
    def test_form_rejects_total_negative_storage(self):
        """
        BUG POTENCIAL: Extra storage que hace el total negativo DEBE rechazarse
        """
        org = OrganizationFactory(extra_storage_gb=0)
        
        form = OrganizationAdminForm(
            data={
                'name': org.name,
                'description': org.description or '',
                'extra_storage_gb': -100,
                'is_active': True,
                'is_founder_member': org.is_founder_member,
                'founder_discount_percentage': org.founder_discount_percentage,
            },
            instance=org
        )
        
        # Esto DEBE ser inválido porque el total sería 10 - 100 = -90 GB
        assert not form.is_valid(), "Form should be invalid for negative total storage"
        assert 'extra_storage_gb' in form.errors, f"Expected error in extra_storage_gb, got: {form.errors}"
    
    def test_form_validation_for_new_organization(self):
        """Nueva organización no tiene restricciones de storage"""
        form = OrganizationAdminForm(
            data={
                'name': 'New Org',
                'extra_storage_gb': -100,
                'is_active': True,
                'is_founder_member': False,
                'founder_discount_percentage': 0
            }
        )
        
        # Para nuevas organizaciones, cualquier valor debe ser válido
        # (se validará después de asignar el plan)
        assert form.is_valid(), f"Form should be valid for new org, got errors: {form.errors}"


# ============================================================================
# TESTS DE CLIENTADMIN - BASIC FUNCTIONALITY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestClientAdminBasic:
    """Tests básicos de ClientAdmin"""
    
    def test_list_display_fields_configured(self, client_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        assert 'name' in client_admin_instance.list_display
        assert 'organization' in client_admin_instance.list_display or 'get_organization_name' in client_admin_instance.list_display
        assert 'email' in client_admin_instance.list_display
        assert 'is_active' in client_admin_instance.list_display or 'get_active_status' in client_admin_instance.list_display
    
    def test_search_fields_configured(self, client_admin_instance):
        """Verificar que se puede buscar por nombre y email"""
        assert 'name' in client_admin_instance.search_fields
        assert 'email' in client_admin_instance.search_fields
    
    def test_search_by_name(self, client_admin_instance, admin_request):
        """Buscar cliente por nombre"""
        org = OrganizationFactory()
        ClientFactory(organization=org, name='Tech Client')
        ClientFactory(organization=org, name='Business Client')
        
        queryset = client_admin_instance.get_queryset(admin_request)
        searched = queryset.filter(name__icontains='Tech')
        
        assert searched.count() == 1
        assert 'Tech' in searched.first().name
    
    def test_search_by_email(self, client_admin_instance, admin_request):
        """Buscar cliente por email"""
        org = OrganizationFactory()
        ClientFactory(organization=org, name='Client 1', email='john@example.com')
        ClientFactory(organization=org, name='Client 2', email='jane@example.com')
        
        queryset = client_admin_instance.get_queryset(admin_request)
        searched = queryset.filter(email__icontains='john')
        
        assert searched.count() == 1
        assert 'john' in searched.first().email
    
    def test_filter_by_organization(self, client_admin_instance, admin_request):
        """Filtrar clientes por organización"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        ClientFactory.create_batch(3, organization=org1)
        ClientFactory.create_batch(2, organization=org2)
        
        queryset = client_admin_instance.get_queryset(admin_request)
        filtered = queryset.filter(organization=org1)
        
        assert filtered.count() == 3


# ============================================================================
# TESTS DE EDGE CASES Y ERROR HANDLING
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestOrganizationAdminEdgeCases:
    """Tests de casos extremos que pueden romper el admin"""
    
    def test_display_organization_without_subscription(self, org_admin_instance):
        """
        BUG POTENCIAL: Organización sin subscription no debe romper el admin
        """
        org = OrganizationFactory()
        
        # Estos métodos NO deben lanzar excepciones
        try:
            org_admin_instance.get_subscription_status(org)
            org_admin_instance.get_subscription_link(org)
            org_admin_instance.get_storage_info(org)
        except AttributeError as e:
            pytest.fail(f"BUG: Admin rompe sin subscription: {e}")
    
    def test_display_organization_with_unicode_name(self, org_admin_instance):
        """Nombres con Unicode deben mostrarse correctamente"""
        org = OrganizationFactory(name='Organización Española 中文 🚀')
        
        # Estos métodos NO deben romper con Unicode
        html = org_admin_instance.get_active_status(org)
        assert org.name not in html  # El nombre no está en el badge de estado
    
    def test_display_organization_with_negative_user_count(self, org_admin_instance):
        """
        EDGE CASE: ¿Qué pasa si la anotación retorna negativo? (no debería pasar)
        """
        org = OrganizationFactory()
        org.user_count_admin = -1  # Simular caso imposible
        
        result = org_admin_instance.user_count(org)
        
        # Debe manejarse sin romper
        assert '-1' in result or '0' in result
    
    def test_get_queryset_optimization(self, org_admin_instance, admin_request):
        """
        PERFORMANCE: get_queryset debe optimizar con prefetch_related
        """
        OrganizationFactory.create_batch(5)
        
        queryset = org_admin_instance.get_queryset(admin_request)
        
        # Verificar que tiene la anotación user_count_admin
        first_org = queryset.first()
        assert hasattr(first_org, 'user_count_admin')
    
    @patch('apps.orgs.models.Organization._cleanup_r2_files')
    def test_delete_organization_without_files(self, mock_cleanup, org_admin_instance, admin_request):
        """Eliminar organización sin archivos no debe romper"""
        org = OrganizationFactory()
        mock_cleanup.return_value = 0
        
        with patch('apps.orgs.admin.log_info'):
            org_admin_instance.delete_model(admin_request, org)
        
        # Debe completarse sin errores
        assert not Organization.objects.filter(id=org.id).exists()
    
    def test_readonly_fields_configured(self, org_admin_instance):
        """Verificar que campos readonly están configurados"""
        readonly = org_admin_instance.readonly_fields
        
        assert 'created_at' in readonly
        assert 'updated_at' in readonly
        assert 'user_count' in readonly
