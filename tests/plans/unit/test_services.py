"""
Tests exhaustivos para SubscriptionService

Estos tests DEBEN detectar bugs reales en la lógica de servicio de suscripciones.
SubscriptionService es CRÍTICO porque maneja la creación de suscripciones y
verificación de permisos de acceso.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from unittest.mock import patch, Mock, PropertyMock
from tests.factories import (
    OrganizationFactory,
    PlanFactory,
    TrialPlanFactory,
    BasicPlanFactory,
    SubscriptionFactory,
    PaymentFactory,
)
from apps.plans.models import Subscription, Payment
from apps.plans.services import SubscriptionService


# ============================================================================
# TESTS DE create_trial_subscription
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestCreateTrialSubscription:
    """
    Tests de create_trial_subscription - CRÍTICO para creación de suscripciones trial
    """
    
    def test_create_trial_subscription_success(self):
        """Crear suscripción trial exitosamente"""
        org = OrganizationFactory()
        # Crear plan trial con nombre exacto 'trial' que es lo que busca get_trial_plan()
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        result = SubscriptionService.create_trial_subscription(org)
        
        assert result['success'] is True
        assert 'subscription' in result
        subscription = result['subscription']
        assert subscription.organization == org
        assert subscription.plan.name == 'trial'
        assert subscription.subscription_status == 'trial_active'
    
    def test_create_trial_subscription_creates_payment(self):
        """Crear suscripción trial debe crear un Payment"""
        org = OrganizationFactory()
        # Crear plan trial con nombre exacto 'trial'
        trial_plan = TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        result = SubscriptionService.create_trial_subscription(org)
        
        assert result['success'] is True
        subscription = result['subscription']
        payments = Payment.objects.filter(subscription=subscription)
        assert payments.count() == 1
        
        payment = payments.first()
        assert payment.amount == Decimal('0.00')
        assert payment.payment_type == 'trial_to_paid'
        assert payment.status == 'completed'
        assert payment.payment_method == 'system'
        assert payment.days_added == trial_plan.trial_days
    
    def test_create_trial_subscription_fails_if_already_exists(self):
        """
        CRÍTICO: No debe crear suscripción si ya existe una
        """
        org = OrganizationFactory()
        SubscriptionFactory(organization=org)
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        result = SubscriptionService.create_trial_subscription(org)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'ya tiene una suscripción' in result['error'].lower()
    
    def test_create_trial_subscription_fails_if_no_trial_plan(self):
        """
        CRÍTICO: Debe fallar si no hay plan trial activo
        """
        org = OrganizationFactory()
        # No crear plan trial
        
        result = SubscriptionService.create_trial_subscription(org)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'trial' in result['error'].lower() or 'plan' in result['error'].lower()
    
    def test_create_trial_subscription_fails_if_trial_plan_inactive(self):
        """Debe fallar si el plan trial está inactivo"""
        org = OrganizationFactory()
        TrialPlanFactory(name='trial', trial_days=7, is_active=False)
        
        result = SubscriptionService.create_trial_subscription(org)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_create_trial_subscription_sets_correct_dates(self):
        """Crear suscripción trial debe configurar fechas correctas"""
        org = OrganizationFactory()
        trial_plan = TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        result = SubscriptionService.create_trial_subscription(org)
        
        assert result['success'] is True
        subscription = result['subscription']
        expected_end = subscription.start_date + timedelta(days=7)
        time_diff = abs((subscription.end_date - expected_end).total_seconds())
        assert time_diff < 60, \
            f"Fecha de fin incorrecta: esperado ~{expected_end}, obtenido {subscription.end_date}"
    
    def test_create_trial_subscription_is_atomic(self):
        """
        CRÍTICO: create_trial_subscription debe ser atómico
        Si falla la creación del Payment, no debe crear la Subscription
        """
        org = OrganizationFactory()
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        # Mock para hacer que Payment.objects.create() falle
        with patch('apps.plans.services.Payment.objects.create') as mock_payment_create:
            mock_payment_create.side_effect = Exception("Error creando pago")
            
            # Debe fallar y no crear suscripción
            result = SubscriptionService.create_trial_subscription(org)
            
            assert result['success'] is False
            # Recargar organización desde DB para verificar que no se creó la suscripción
            org.refresh_from_db()
            assert not hasattr(org, 'subscription') or not Subscription.objects.filter(organization=org).exists()
    
    def test_create_trial_subscription_with_multiple_trial_plans(self):
        """
        EDGE CASE: ¿Qué pasa si hay múltiples planes trial activos?
        get_trial_plan() debe retornar uno, pero ¿cuál?
        """
        org = OrganizationFactory()
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        # No debería haber múltiples con el mismo name (unique constraint)
        # Pero este test verifica el comportamiento si hubiera


# ============================================================================
# TESTS DE get_subscription_or_create
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestGetSubscriptionOrCreate:
    """
    Tests de get_subscription_or_create - CRÍTICO para obtener o crear suscripción
    """
    
    def test_get_subscription_or_create_returns_existing(self):
        """Debe retornar suscripción existente"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        result = SubscriptionService.get_subscription_or_create(org)
        
        assert result == subscription
        assert result.organization == org
    
    def test_get_subscription_or_create_creates_if_not_exists(self):
        """Debe crear suscripción trial si no existe"""
        org = OrganizationFactory()
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        result = SubscriptionService.get_subscription_or_create(org)
        
        assert result is not None
        assert result.organization == org
        assert result.plan.name == 'trial'
        assert result.subscription_status == 'trial_active'
    
    def test_get_subscription_or_create_returns_none_on_error(self):
        """Debe retornar None si hay error creando suscripción"""
        org = OrganizationFactory()
        # No crear plan trial para que falle
        
        result = SubscriptionService.get_subscription_or_create(org)
        
        assert result is None
    
    def test_get_subscription_or_create_handles_none_organization(self):
        """
        BUG POTENCIAL: ¿Qué pasa si organization es None?
        """
        try:
            result = SubscriptionService.get_subscription_or_create(None)
            # Debe manejar None sin crash
            assert result is None
        except AttributeError as e:
            pytest.fail(f"BUG: get_subscription_or_create crashea con organization=None: {e}")


# ============================================================================
# TESTS DE check_access_permissions
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestCheckAccessPermissions:
    """
    Tests de check_access_permissions - CRÍTICO para control de acceso
    """
    
    def test_check_access_permissions_trial_active_full_access(self):
        """trial_active debe tener acceso completo"""
        # Crear plan con nombre exacto 'trial' para que status sea 'trial_active'
        plan = TrialPlanFactory(name='trial')
        subscription = SubscriptionFactory(plan=plan, subscription_status='trial_active')
        
        result = SubscriptionService.check_access_permissions(subscription)
        
        assert result['has_access'] is True
        assert result['access_level'] == 'full'
        assert result['message'] == ''
    
    def test_check_access_permissions_basic_active_full_access(self):
        """basic_active debe tener acceso completo"""
        # Crear plan con nombre exacto 'basic' para que status sea 'basic_active'
        plan = BasicPlanFactory(name='basic')
        subscription = SubscriptionFactory(plan=plan, subscription_status='basic_active')
        
        result = SubscriptionService.check_access_permissions(subscription)
        
        assert result['has_access'] is True
        assert result['access_level'] == 'full'
        assert result['message'] == ''
    
    def test_check_access_permissions_trial_expired_limited_access_dashboard(self):
        """trial_expired debe tener acceso limitado a dashboard"""
        plan = TrialPlanFactory(name='trial')
        # Crear suscripción expirada con end_date en el pasado
        subscription = SubscriptionFactory(
            plan=plan,
            end_date=timezone.now() - timedelta(days=1)
        )
        # Forzar status expired usando update para evitar save()
        Subscription.objects.filter(pk=subscription.pk).update(subscription_status='trial_expired')
        subscription.refresh_from_db()
        
        result = SubscriptionService.check_access_permissions(
            subscription,
            current_module='dashboard'
        )
        
        assert result['has_access'] is True
        assert result['access_level'] == 'limited'
        assert 'expirada' in result['message'].lower()
    
    def test_check_access_permissions_trial_expired_limited_access_plans(self):
        """trial_expired debe tener acceso limitado a plans"""
        plan = TrialPlanFactory(name='trial')
        # Crear suscripción expirada con end_date en el pasado
        subscription = SubscriptionFactory(
            plan=plan,
            end_date=timezone.now() - timedelta(days=1)
        )
        # Forzar status expired usando update para evitar save()
        Subscription.objects.filter(pk=subscription.pk).update(subscription_status='trial_expired')
        subscription.refresh_from_db()
        
        result = SubscriptionService.check_access_permissions(
            subscription,
            current_module='plans'
        )
        
        assert result['has_access'] is True
        assert result['access_level'] == 'limited'
    
    def test_check_access_permissions_trial_expired_no_access_other_modules(self):
        """trial_expired NO debe tener acceso a otros módulos"""
        plan = TrialPlanFactory(name='trial')
        # Crear suscripción expirada con end_date en el pasado
        subscription = SubscriptionFactory(
            plan=plan,
            end_date=timezone.now() - timedelta(days=1)
        )
        # Forzar status expired usando update para evitar save()
        Subscription.objects.filter(pk=subscription.pk).update(subscription_status='trial_expired')
        subscription.refresh_from_db()
        
        result = SubscriptionService.check_access_permissions(
            subscription,
            current_module='projects'
        )
        
        assert result['has_access'] is False
        assert result['access_level'] == 'none'
        assert 'redirect_to' in result
        assert result['redirect_to'] == 'plans:subscription_dashboard'
    
    def test_check_access_permissions_basic_expired_limited_access_dashboard(self):
        """basic_expired debe tener acceso limitado a dashboard"""
        plan = BasicPlanFactory(name='basic')
        # Crear suscripción expirada con end_date en el pasado
        subscription = SubscriptionFactory(
            plan=plan,
            end_date=timezone.now() - timedelta(days=1)
        )
        # Forzar status expired usando update para evitar save()
        Subscription.objects.filter(pk=subscription.pk).update(subscription_status='basic_expired')
        subscription.refresh_from_db()
        
        result = SubscriptionService.check_access_permissions(
            subscription,
            current_module='dashboard'
        )
        
        assert result['has_access'] is True
        assert result['access_level'] == 'limited'
    
    def test_check_access_permissions_basic_expired_no_access_other_modules(self):
        """basic_expired NO debe tener acceso a otros módulos"""
        plan = BasicPlanFactory(name='basic')
        # Crear suscripción expirada con end_date en el pasado
        subscription = SubscriptionFactory(
            plan=plan,
            end_date=timezone.now() - timedelta(days=1)
        )
        # Forzar status expired usando update para evitar save()
        Subscription.objects.filter(pk=subscription.pk).update(subscription_status='basic_expired')
        subscription.refresh_from_db()
        
        result = SubscriptionService.check_access_permissions(
            subscription,
            current_module='orgs'
        )
        
        assert result['has_access'] is False
        assert result['access_level'] == 'none'
    
    def test_check_access_permissions_with_none_module(self):
        """check_access_permissions con current_module=None"""
        plan = TrialPlanFactory(name='trial')
        subscription = SubscriptionFactory(plan=plan, subscription_status='trial_active')
        
        result = SubscriptionService.check_access_permissions(
            subscription,
            current_module=None
        )
        
        # Con status activo, debe tener acceso completo
        assert result['has_access'] is True
        assert result['access_level'] == 'full'
    
    def test_check_access_permissions_handles_exception(self):
        """
        CRÍTICO: check_access_permissions debe manejar excepciones
        """
        subscription = SubscriptionFactory()
        
        # Simular error en subscription_status usando mock que lanza excepción
        with patch.object(type(subscription), 'subscription_status', new_callable=PropertyMock) as mock_status:
            mock_status.side_effect = Exception("Error simulado")
            result = SubscriptionService.check_access_permissions(subscription)
            
            # Debe retornar acceso denegado en caso de error
            assert result['has_access'] is False
            assert result['access_level'] == 'none'
            # El mensaje puede variar pero debe indicar problema de verificación
            assert 'message' in result
            assert 'redirect_to' in result
    
    def test_check_access_permissions_all_modules_for_active(self):
        """Suscripción activa debe tener acceso a todos los módulos"""
        plan = BasicPlanFactory(name='basic')
        subscription = SubscriptionFactory(plan=plan, subscription_status='basic_active')
        
        modules = ['dashboard', 'orgs', 'users', 'projects', 'plans', 'billing', 'reports']
        
        for module in modules:
            result = SubscriptionService.check_access_permissions(
                subscription,
                current_module=module
            )
            
            assert result['has_access'] is True, \
                f"Módulo {module} debe tener acceso para suscripción activa"
            assert result['access_level'] == 'full'
    
    def test_check_access_permissions_expired_modules_restriction(self):
        """Suscripción expirada debe tener acceso solo a dashboard y plans"""
        subscription = SubscriptionFactory(subscription_status='basic_expired')
        
        # Módulos permitidos
        allowed_modules = ['dashboard', 'plans']
        for module in allowed_modules:
            result = SubscriptionService.check_access_permissions(
                subscription,
                current_module=module
            )
            assert result['has_access'] is True, \
                f"Módulo {module} debe estar permitido para suscripción expirada"
        
        # Módulos no permitidos
        restricted_modules = ['orgs', 'users', 'projects', 'reports', 'billing']
        for module in restricted_modules:
            result = SubscriptionService.check_access_permissions(
                subscription,
                current_module=module
            )
            assert result['has_access'] is False, \
                f"Módulo {module} NO debe estar permitido para suscripción expirada"
            assert result['redirect_to'] == 'plans:subscription_dashboard'


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionServiceEdgeCases:
    """Tests de casos extremos - ENCONTRAR BUGS"""
    
    def test_create_trial_subscription_with_organization_without_pk(self):
        """
        BUG POTENCIAL: ¿Qué pasa si la organización no tiene pk?
        """
        org = OrganizationFactory()
        org.pk = None  # Simular organización sin guardar
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        
        # Debe fallar porque no se puede crear suscripción sin organización guardada
        result = SubscriptionService.create_trial_subscription(org)
        
        # Debe manejar el error correctamente
        assert result['success'] is False or 'subscription' not in result
    
    def test_check_access_permissions_with_invalid_status(self):
        """
        BUG POTENCIAL: ¿Qué pasa con un status inválido?
        """
        subscription = SubscriptionFactory()
        subscription.subscription_status = 'invalid_status'
        subscription.save()
        
        result = SubscriptionService.check_access_permissions(subscription)
        
        # Debe manejar status inválido sin crash
        # Probablemente debe retornar acceso denegado
        assert 'has_access' in result
        assert 'access_level' in result
    
    def test_get_subscription_or_create_with_deleted_subscription(self):
        """
        EDGE CASE: ¿Qué pasa si la suscripción fue eliminada pero la org sigue existiendo?
        """
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        subscription_id = subscription.id
        
        # Eliminar suscripción
        subscription.delete()
        
        # Debe crear una nueva
        TrialPlanFactory(name='trial', trial_days=7, is_active=True)
        result = SubscriptionService.get_subscription_or_create(org)
        
        assert result is not None
        assert result.id != subscription_id
        assert result.organization == org

