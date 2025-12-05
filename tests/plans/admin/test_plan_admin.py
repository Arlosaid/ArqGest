"""
Tests exhaustivos para PlanAdmin, SubscriptionAdmin, PaymentAdmin,
UpgradeRequestAdmin y RenewalRequestAdmin - Panel de administración Django

Estos tests DEBEN detectar bugs reales en la lógica del admin, no solo validar el happy path.
Incluyen validaciones, permisos, acciones personalizadas, edge cases y manejo de errores.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from unittest.mock import patch, Mock, MagicMock
from apps.plans.admin import (
    PlanAdmin,
    SubscriptionAdmin,
    PaymentAdmin,
    UpgradeRequestAdmin,
    RenewalRequestAdmin,
    ExtendSubscriptionForm,
    ChangePlanForm,
)
from apps.plans.models import Plan, Subscription, Payment, UpgradeRequest, RenewalRequest
from tests.factories import (
    OrganizationFactory,
    PlanFactory,
    TrialPlanFactory,
    BasicPlanFactory,
    SubscriptionFactory,
    PaymentFactory,
    SuperUserFactory,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_site():
    """Fixture que proporciona una instancia de AdminSite"""
    return AdminSite()


@pytest.fixture
def admin_user(db):
    """Fixture que crea un superusuario"""
    return SuperUserFactory(email='admin@test.com')


@pytest.fixture
def plan_admin_instance(admin_site):
    """Fixture que proporciona una instancia de PlanAdmin"""
    return PlanAdmin(Plan, admin_site)


@pytest.fixture
def subscription_admin_instance(admin_site):
    """Fixture que proporciona una instancia de SubscriptionAdmin"""
    return SubscriptionAdmin(Subscription, admin_site)


@pytest.fixture
def payment_admin_instance(admin_site):
    """Fixture que proporciona una instancia de PaymentAdmin"""
    return PaymentAdmin(Payment, admin_site)


@pytest.fixture
def upgrade_request_admin_instance(admin_site):
    """Fixture que proporciona una instancia de UpgradeRequestAdmin"""
    return UpgradeRequestAdmin(UpgradeRequest, admin_site)


@pytest.fixture
def renewal_request_admin_instance(admin_site):
    """Fixture que proporciona una instancia de RenewalRequestAdmin"""
    return RenewalRequestAdmin(RenewalRequest, admin_site)


@pytest.fixture
def admin_request(admin_user):
    """Fixture que crea un request con usuario admin autenticado"""
    factory = RequestFactory()
    request = factory.get('/admin/plans/plan/')
    request.user = admin_user
    
    # Añadir session y messages
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    return request


# ============================================================================
# TESTS DE PLANADMIN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPlanAdminListDisplay:
    """Tests de visualización de lista en PlanAdmin"""
    
    def test_list_display_fields_configured(self, plan_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        expected_fields = [
            'display_name', 'name', 'price', 'max_users', 'max_storage_gb',
            'trial_days', 'billing_cycle_days', 'is_active'
        ]
        
        assert list(plan_admin_instance.list_display) == expected_fields
    
    def test_list_filter_configured(self, plan_admin_instance):
        """Verificar que list_filter está configurado"""
        expected_filters = ['is_active', 'name']
        
        assert set(plan_admin_instance.list_filter) == set(expected_filters)
    
    def test_search_fields_configured(self, plan_admin_instance):
        """Verificar que search_fields está configurado"""
        expected_fields = ['name', 'display_name']
        
        assert set(plan_admin_instance.search_fields) == set(expected_fields)
    
    def test_readonly_fields_configured(self, plan_admin_instance):
        """Verificar que readonly_fields está configurado"""
        expected_fields = ['created_at', 'updated_at']
        
        assert set(plan_admin_instance.readonly_fields) == set(expected_fields)


@pytest.mark.django_db
@pytest.mark.unit
class TestPlanAdminSaveModel:
    """Tests de save_model en PlanAdmin"""
    
    @patch('apps.plans.admin.log_info')
    def test_save_model_logs_creation(self, mock_log, plan_admin_instance, admin_request):
        """Crear nuevo plan debe generar log"""
        plan = Plan(
            name='trial',
            display_name='Trial Plan',
            price=Decimal('0.00'),
            max_users=1,
            max_storage_gb=10,
            trial_days=7
        )
        
        plan_admin_instance.save_model(admin_request, plan, None, change=False)
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs['event'] == 'PLAN_CREATED'
        assert call_kwargs['plan_name'] == 'Trial Plan'
    
    @patch('apps.plans.admin.log_info')
    def test_save_model_logs_update_with_changes(self, mock_log, plan_admin_instance, admin_request):
        """Actualizar plan debe generar log con cambios"""
        plan = PlanFactory(price=Decimal('299.00'))
        
        plan.price = Decimal('349.00')
        plan_admin_instance.save_model(admin_request, plan, None, change=True)
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs['event'] == 'PLAN_UPDATED'
        assert 'changes' in call_kwargs
    
    @patch('apps.plans.admin.log_error')
    def test_save_model_logs_error_on_failure(self, mock_log_error, plan_admin_instance, admin_request):
        """Error al guardar debe generar log de error"""
        plan = PlanFactory()
        
        # Simular error al guardar
        with patch.object(plan, 'save', side_effect=Exception("Error de BD")):
            try:
                plan_admin_instance.save_model(admin_request, plan, None, change=True)
            except Exception:
                pass
        
        # Verificar que se llamó al log de error
        assert mock_log_error.called
        call_kwargs = mock_log_error.call_args[1]
        assert call_kwargs['event'] == 'PLAN_SAVE_FAILED'


# ============================================================================
# TESTS DE SUBSCRIPTIONADMIN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAdminListDisplay:
    """Tests de visualización de lista en SubscriptionAdmin"""
    
    def test_list_display_fields_configured(self, subscription_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        expected_fields = [
            'organization', 'get_founder_indicator', 'plan', 'subscription_status',
            'end_date_formatted', 'days_remaining_display', 'get_add_user_link', 'is_active'
        ]
        
        assert list(subscription_admin_instance.list_display) == expected_fields
    
    def test_list_filter_configured(self, subscription_admin_instance):
        """Verificar que list_filter está configurado"""
        from apps.plans.admin import ExpiringSoonFilter
        expected_filters = [
            'subscription_status', 'plan__name', 'organization__is_founder_member', ExpiringSoonFilter
        ]
        
        assert set(subscription_admin_instance.list_filter) == set(expected_filters)
    
    def test_search_fields_configured(self, subscription_admin_instance):
        """Verificar que search_fields está configurado"""
        expected_fields = ['organization__name', 'plan__display_name']
        
        assert set(subscription_admin_instance.search_fields) == set(expected_fields)
    
    def test_get_founder_indicator_shows_for_founder(self, subscription_admin_instance):
        """get_founder_indicator debe mostrar badge para organizaciones fundadoras"""
        org = OrganizationFactory(is_founder_member=True)
        subscription = SubscriptionFactory(organization=org)
        
        html = subscription_admin_instance.get_founder_indicator(subscription)
        
        assert 'FUNDADOR' in html
        assert '$199' in html
    
    def test_get_founder_indicator_shows_dash_for_non_founder(self, subscription_admin_instance):
        """get_founder_indicator debe mostrar '-' para organizaciones no fundadoras"""
        org = OrganizationFactory(is_founder_member=False)
        subscription = SubscriptionFactory(organization=org)
        
        html = subscription_admin_instance.get_founder_indicator(subscription)
        
        assert html == '-'
    
    def test_end_date_formatted_shows_correct_format(self, subscription_admin_instance):
        """end_date_formatted debe mostrar fecha formateada"""
        subscription = SubscriptionFactory()
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()
        
        formatted = subscription_admin_instance.end_date_formatted(subscription)
        
        assert 'México' in formatted
        assert formatted != "N/A"
    
    def test_end_date_formatted_shows_na_for_none(self, subscription_admin_instance):
        """end_date_formatted debe mostrar 'N/A' si end_date es None"""
        subscription = SubscriptionFactory()
        subscription.end_date = None
        subscription.save()
        
        formatted = subscription_admin_instance.end_date_formatted(subscription)
        
        assert formatted == "N/A"
    
    def test_days_remaining_display_shows_days(self, subscription_admin_instance):
        """days_remaining_display debe mostrar días restantes"""
        subscription = SubscriptionFactory()
        subscription.end_date = timezone.now() + timedelta(days=10)
        subscription.subscription_status = 'basic_active'
        subscription.save()
        
        display = subscription_admin_instance.days_remaining_display(subscription)
        
        assert 'día' in display.lower()
    
    def test_days_remaining_display_shows_expired(self, subscription_admin_instance):
        """days_remaining_display debe mostrar 'Expirado' si está expirado"""
        subscription = SubscriptionFactory()
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.subscription_status = 'basic_expired'
        subscription.save()
        
        display = subscription_admin_instance.days_remaining_display(subscription)
        
        assert 'Expirado' in display or 'expired' in display.lower()


@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAdminActions:
    """Tests de acciones personalizadas de SubscriptionAdmin"""
    
    def test_extend_subscription_action_exists(self, subscription_admin_instance):
        """La acción extend_subscription_action debe existir"""
        assert hasattr(subscription_admin_instance, 'extend_subscription_action')
        assert 'extend_subscription_action' in subscription_admin_instance.actions
    
    def test_change_plan_action_exists(self, subscription_admin_instance):
        """La acción change_plan_action debe existir"""
        assert hasattr(subscription_admin_instance, 'change_plan_action')
        assert 'change_plan_action' in subscription_admin_instance.actions
    
    def test_process_selected_payments_action_exists(self, subscription_admin_instance):
        """La acción process_selected_payments debe existir"""
        assert hasattr(subscription_admin_instance, 'process_selected_payments')
        assert 'process_selected_payments' in subscription_admin_instance.actions


@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAdminSaveModel:
    """Tests de save_model en SubscriptionAdmin"""
    
    @patch('apps.plans.admin.log_info')
    def test_save_model_logs_creation(self, mock_log, subscription_admin_instance, admin_request):
        """Crear nueva suscripción debe generar log"""
        org = OrganizationFactory()
        plan = BasicPlanFactory()
        subscription = Subscription(
            organization=org,
            plan=plan
        )
        
        subscription_admin_instance.save_model(admin_request, subscription, None, change=False)
        
        # Verificar que se llamó al log
        assert mock_log.called
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs['event'] == 'SUBSCRIPTION_CREATED'
    
    @patch('apps.plans.models.Subscription.switch_plan')
    def test_save_model_calls_switch_plan_on_plan_change(self, mock_switch_plan, subscription_admin_instance, admin_request):
        """Cambiar plan debe llamar a switch_plan"""
        subscription = SubscriptionFactory()
        new_plan = PlanFactory(name='new-unique-plan')  # Nombre único para evitar duplicados
        
        subscription.plan = new_plan
        subscription_admin_instance.save_model(admin_request, subscription, None, change=True)
        
        # Verificar que se llamó a switch_plan
        mock_switch_plan.assert_called_once()
    
    @patch('apps.plans.models.Subscription.update_status')
    def test_save_model_calls_update_status(self, mock_update_status, subscription_admin_instance, admin_request):
        """Guardar suscripción debe llamar a update_status"""
        subscription = SubscriptionFactory()
        
        subscription_admin_instance.save_model(admin_request, subscription, None, change=True)
        
        # Verificar que se llamó a update_status
        mock_update_status.assert_called_once()


# ============================================================================
# TESTS DE PAYMENTADMIN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentAdmin:
    """Tests de PaymentAdmin"""
    
    def test_list_display_fields_configured(self, payment_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        expected_fields = [
            'get_organization_name', 'get_amount_formatted', 'payment_type', 'payment_method',
            'status', 'processed_by', 'created_at', 'description'
        ]
        
        assert payment_admin_instance.list_display == expected_fields
    
    def test_list_filter_configured(self, payment_admin_instance):
        """Verificar que list_filter está configurado"""
        expected_filters = ['status', 'payment_method', 'payment_type', 'created_at']
        
        assert set(payment_admin_instance.list_filter) == set(expected_filters)
    
    def test_has_add_permission_returns_false(self, payment_admin_instance, admin_request):
        """has_add_permission debe retornar False (solo lectura)"""
        assert payment_admin_instance.has_add_permission(admin_request) is False
    
    def test_has_change_permission_returns_false(self, payment_admin_instance, admin_request):
        """has_change_permission debe retornar False (solo lectura)"""
        payment = PaymentFactory()
        assert payment_admin_instance.has_change_permission(admin_request, payment) is False
    
    def test_readonly_fields_configured(self, payment_admin_instance):
        """Verificar que readonly_fields está configurado"""
        expected_fields = [
            'subscription', 'amount', 'payment_method', 'payment_type', 'status',
            'processed_by', 'description', 'days_added', 'old_end_date',
            'new_end_date', 'created_at'
        ]
        
        assert set(payment_admin_instance.readonly_fields) == set(expected_fields)


# ============================================================================
# TESTS DE UPGRADEREQUESTADMIN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestUpgradeRequestAdminListDisplay:
    """Tests de visualización de lista en UpgradeRequestAdmin"""
    
    def test_list_display_fields_configured(self, upgrade_request_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        expected_fields = [
            'organization', 'current_plan', 'requested_plan', 'amount',
            'status_display', 'created_at', 'approved_by', 'actions_column'
        ]
        
        assert upgrade_request_admin_instance.list_display == expected_fields
    
    def test_list_filter_configured(self, upgrade_request_admin_instance):
        """Verificar que list_filter está configurado"""
        expected_filters = ['status', 'created_at']
        
        assert set(upgrade_request_admin_instance.list_filter) == set(expected_filters)
    
    def test_status_display_shows_colors(self, upgrade_request_admin_instance):
        """status_display debe mostrar colores según el estado"""
        org = OrganizationFactory()
        current_plan = TrialPlanFactory()
        requested_plan = BasicPlanFactory()
        
        # Pendiente
        request = UpgradeRequest.objects.create(
            organization=org,
            current_plan=current_plan,
            requested_plan=requested_plan,
            amount=Decimal('299.00'),
            status='pending'
        )
        
        html = upgrade_request_admin_instance.status_display(request)
        assert 'Pendiente' in html or 'pending' in html.lower()
        
        # Aprobado
        request.status = 'approved'
        request.save()
        html = upgrade_request_admin_instance.status_display(request)
        assert 'Aprobado' in html or 'approved' in html.lower()
        
        # Rechazado
        request.status = 'rejected'
        request.save()
        html = upgrade_request_admin_instance.status_display(request)
        assert 'Rechazado' in html or 'rejected' in html.lower()
    
    def test_actions_column_shows_buttons_for_pending(self, upgrade_request_admin_instance):
        """actions_column debe mostrar botones para solicitudes pendientes"""
        org = OrganizationFactory()
        current_plan = TrialPlanFactory()
        requested_plan = BasicPlanFactory()
        
        request = UpgradeRequest.objects.create(
            organization=org,
            current_plan=current_plan,
            requested_plan=requested_plan,
            amount=Decimal('299.00'),
            status='pending'
        )
        
        html = upgrade_request_admin_instance.actions_column(request)
        assert 'Aprobar' in html or 'approve' in html.lower()
        assert 'Rechazar' in html or 'reject' in html.lower()
    
    def test_actions_column_shows_dash_for_non_pending(self, upgrade_request_admin_instance):
        """actions_column debe mostrar '-' para solicitudes no pendientes"""
        org = OrganizationFactory()
        current_plan = TrialPlanFactory()
        requested_plan = BasicPlanFactory()
        
        request = UpgradeRequest.objects.create(
            organization=org,
            current_plan=current_plan,
            requested_plan=requested_plan,
            amount=Decimal('299.00'),
            status='approved'
        )
        
        html = upgrade_request_admin_instance.actions_column(request)
        assert '—' in html or '-' in html


@pytest.mark.django_db
@pytest.mark.unit
class TestUpgradeRequestAdminActions:
    """Tests de acciones de UpgradeRequestAdmin"""
    
    def test_approve_selected_requests_action_exists(self, upgrade_request_admin_instance):
        """La acción approve_selected_requests debe existir"""
        assert hasattr(upgrade_request_admin_instance, 'approve_selected_requests')
        assert 'approve_selected_requests' in upgrade_request_admin_instance.actions
    
    def test_reject_selected_requests_action_exists(self, upgrade_request_admin_instance):
        """La acción reject_selected_requests debe existir"""
        assert hasattr(upgrade_request_admin_instance, 'reject_selected_requests')
        assert 'reject_selected_requests' in upgrade_request_admin_instance.actions


# ============================================================================
# TESTS DE RENEWALREQUESTADMIN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestRenewalRequestAdminListDisplay:
    """Tests de visualización de lista en RenewalRequestAdmin"""
    
    def test_list_display_fields_configured(self, renewal_request_admin_instance):
        """Verificar que list_display tiene los campos correctos"""
        expected_fields = [
            'organization', 'subscription', 'renewal_amount', 'renewal_days',
            'status', 'created_at', 'processed_at', 'approved_by'
        ]
        
        assert renewal_request_admin_instance.list_display == expected_fields
    
    def test_list_filter_configured(self, renewal_request_admin_instance):
        """Verificar que list_filter está configurado"""
        expected_filters = ['status', 'created_at', 'processed_at']
        
        assert set(renewal_request_admin_instance.list_filter) == set(expected_filters)
    
    def test_approve_selected_renewals_action_exists(self, renewal_request_admin_instance):
        """La acción approve_selected_renewals debe existir"""
        assert hasattr(renewal_request_admin_instance, 'approve_selected_renewals')
        assert 'approve_selected_renewals' in renewal_request_admin_instance.actions
    
    def test_reject_selected_renewals_action_exists(self, renewal_request_admin_instance):
        """La acción reject_selected_renewals debe existir"""
        assert hasattr(renewal_request_admin_instance, 'reject_selected_renewals')
        assert 'reject_selected_renewals' in renewal_request_admin_instance.actions
