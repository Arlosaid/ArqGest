"""
Tests exhaustivos para decorators de orgs

Estos decorators controlan SEGURIDAD y PERMISOS. Los tests DEBEN detectar bugs
que podrían permitir acceso no autorizado o bypassear límites.
"""
import json
import pytest
from django.test import RequestFactory
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.messages import get_messages
from django.shortcuts import redirect
from unittest.mock import Mock, patch
from apps.orgs.decorators import (
    check_user_limit,
    require_org_admin,
    require_active_subscription,
    require_plan_feature,
    validate_organization_context
)
from tests.factories import (
    UserFactory,
    SuperUserFactory,
    OrganizationFactory,
    PlanFactory,
    SubscriptionFactory
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def request_factory():
    """Fixture que proporciona RequestFactory"""
    return RequestFactory()


@pytest.fixture
def mock_view():
    """Fixture que proporciona una vista mock"""
    def view(request, *args, **kwargs):
        return JsonResponse({'success': True})
    return view


# ============================================================================
# TESTS DE check_user_limit
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestCheckUserLimitDecorator:
    """
    Tests del decorador check_user_limit - CRÍTICO para límites de usuarios
    """
    
    def test_allows_get_requests_without_checking(self, request_factory, mock_view, disable_account_signals):
        """GET requests no deben verificar límites"""
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Simular request GET
        request = request_factory.get('/users/create/')
        request.user = user
        
        decorated = check_user_limit(mock_view)
        response = decorated(request)
        
        # Debe pasar sin verificar límites
        assert response.status_code == 200
    
    def test_allows_post_when_under_limit(self, request_factory, mock_view, disable_account_signals):
        """POST debe pasar si no se ha alcanzado el límite"""
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock: organización puede añadir usuarios
        with patch.object(org, 'can_add_user', return_value=True):
            request = request_factory.post('/users/create/')
            request.user = user
            request.user.organization = org
            
            decorated = check_user_limit(mock_view)
            response = decorated(request)
        
        assert response.status_code == 200
    
    def test_blocks_post_when_at_limit(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: POST debe bloquearse si se alcanzó el límite
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock: organización NO puede añadir usuarios
        with patch.object(org, 'can_add_user', return_value=False):
            with patch.object(org, 'can_add_user_detailed', return_value={
                'can_add': False,
                'total_users': 1,
                'active_users': 1,
                'inactive_users': 0,
                'has_inactive_users': False
            }):
                with patch.object(org, 'get_max_users', return_value=1):
                    request = request_factory.post('/users/create/')
                    request.user = user
                    request.user.organization = org
                    setattr(request, 'session', {})
                    from django.contrib.messages.storage.fallback import FallbackStorage
                    setattr(request, '_messages', FallbackStorage(request))
                    
                    decorated = check_user_limit(mock_view)
                    response = decorated(request)
        
        # Debe redirigir a la lista de usuarios
        assert response.status_code == 302
        assert '/users/' in response.url or 'user_list' in response.url
    
    def test_blocks_ajax_post_when_at_limit(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Requests AJAX deben retornar JSON error cuando están al límite
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock: organización NO puede añadir usuarios
        with patch.object(org, 'can_add_user', return_value=False):
            with patch.object(org, 'can_add_user_detailed', return_value={
                'can_add': False,
                'total_users': 1,
                'active_users': 1,
                'inactive_users': 0,
                'has_inactive_users': False
            }):
                with patch.object(org, 'get_max_users', return_value=1):
                    request = request_factory.post(
                        '/users/create/',
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                    )
                    request.user = user
                    request.user.organization = org
                    
                    decorated = check_user_limit(mock_view)
                    response = decorated(request)
        
        # Debe retornar JSON con error
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['success'] is False
        assert 'límite' in data['error'].lower()
    
    def test_suggests_reactivate_inactive_users(self, request_factory, mock_view, disable_account_signals):
        """
        Debe sugerir reactivar usuarios inactivos si existen
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock: hay usuarios inactivos
        with patch.object(org, 'can_add_user', return_value=False):
            with patch.object(org, 'can_add_user_detailed', return_value={
                'can_add': False,
                'total_users': 1,
                'active_users': 0,
                'inactive_users': 1,
                'has_inactive_users': True
            }):
                with patch.object(org, 'get_max_users', return_value=1):
                    request = request_factory.post('/users/create/')
                    request.user = user
                    request.user.organization = org
                    setattr(request, 'session', {})
                    from django.contrib.messages.storage.fallback import FallbackStorage
                    setattr(request, '_messages', FallbackStorage(request))
                    
                    decorated = check_user_limit(mock_view)
                    response = decorated(request)
                    
                    # Verificar que el mensaje menciona reactivar usuarios
                    messages = list(get_messages(request))
                    assert any('reactivar' in str(m).lower() for m in messages)
    
    def test_allows_user_without_organization(self, request_factory, mock_view, disable_account_signals):
        """Usuario sin organización debe pasar (superuser scenario)"""
        user = SuperUserFactory()
        
        request = request_factory.post('/users/create/')
        request.user = user
        request.user.organization = None
        
        decorated = check_user_limit(mock_view)
        response = decorated(request)
        
        # Debe pasar sin verificar límites
        assert response.status_code == 200


# ============================================================================
# TESTS DE require_org_admin
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestRequireOrgAdminDecorator:
    """
    Tests del decorador require_org_admin - CRÍTICO para permisos
    """
    
    def test_allows_org_admin(self, request_factory, mock_view, disable_account_signals):
        """Administrador de org debe tener acceso"""
        org = OrganizationFactory()
        user = UserFactory(organization=org, is_org_admin=True)
        
        request = request_factory.get('/admin-only/')
        request.user = user
        
        decorated = require_org_admin(mock_view)
        response = decorated(request)
        
        assert response.status_code == 200
    
    def test_allows_superuser(self, request_factory, mock_view):
        """Superuser debe tener acceso siempre"""
        user = SuperUserFactory()
        
        request = request_factory.get('/admin-only/')
        request.user = user
        
        decorated = require_org_admin(mock_view)
        response = decorated(request)
        
        assert response.status_code == 200
    
    def test_blocks_non_admin(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Usuario NO admin debe ser bloqueado
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org, is_org_admin=False)
        
        request = request_factory.get('/admin-only/')
        request.user = user
        
        decorated = require_org_admin(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request)
    
    def test_blocks_unauthenticated_user(self, request_factory, mock_view):
        """
        CRÍTICO: Usuario no autenticado debe ser bloqueado
        """
        from django.contrib.auth.models import AnonymousUser
        
        request = request_factory.get('/admin-only/')
        request.user = AnonymousUser()
        
        decorated = require_org_admin(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request)
    
    def test_blocks_user_without_organization(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Usuario sin organización debe ser bloqueado (excepto superuser)
        """
        user = UserFactory(organization=None, is_org_admin=True)
        
        request = request_factory.get('/admin-only/')
        request.user = user
        
        decorated = require_org_admin(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request)
    
    def test_blocks_ajax_non_admin(self, request_factory, mock_view, disable_account_signals):
        """
        AJAX request de NO admin debe retornar JSON error
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org, is_org_admin=False)
        
        request = request_factory.get(
            '/admin-only/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = user
        
        decorated = require_org_admin(mock_view)
        response = decorated(request)
        
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['success'] is False
        assert data['permission_denied'] is True


# ============================================================================
# TESTS DE require_active_subscription
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestRequireActiveSubscriptionDecorator:
    """
    Tests del decorador require_active_subscription - CRÍTICO para acceso
    """
    
    def test_allows_active_subscription(self, request_factory, mock_view, disable_account_signals):
        """Suscripción activa debe permitir acceso"""
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock de subscription activa
        mock_subscription = Mock()
        mock_subscription.is_active = True
        
        with patch.object(org, 'get_subscription', return_value=mock_subscription):
            request = request_factory.get('/feature/')
            request.user = user
            request.user.organization = org
            
            decorated = require_active_subscription(mock_view)
            response = decorated(request)
        
        assert response.status_code == 200
    
    def test_allows_superuser_without_subscription(self, request_factory, mock_view):
        """Superuser debe tener acceso incluso sin suscripción"""
        user = SuperUserFactory()
        
        request = request_factory.get('/feature/')
        request.user = user
        
        decorated = require_active_subscription(mock_view)
        response = decorated(request)
        
        assert response.status_code == 200
    
    def test_blocks_inactive_subscription(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Suscripción inactiva debe bloquear acceso
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock de subscription inactiva
        mock_subscription = Mock()
        mock_subscription.is_active = False
        
        with patch.object(org, 'get_subscription', return_value=mock_subscription):
            request = request_factory.get('/feature/')
            request.user = user
            request.user.organization = org
            setattr(request, 'session', {})
            from django.contrib.messages.storage.fallback import FallbackStorage
            setattr(request, '_messages', FallbackStorage(request))
            
            decorated = require_active_subscription(mock_view)
            response = decorated(request)
        
        # Debe redirigir al dashboard de planes/suscripciones
        assert response.status_code == 302
        assert '/plans/dashboard/' in response.url or 'subscription_dashboard' in response.url
    
    def test_blocks_without_subscription(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Sin suscripción debe bloquear acceso
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        with patch.object(org, 'get_subscription', return_value=None):
            request = request_factory.get('/feature/')
            request.user = user
            request.user.organization = org
            setattr(request, 'session', {})
            from django.contrib.messages.storage.fallback import FallbackStorage
            setattr(request, '_messages', FallbackStorage(request))
            
            decorated = require_active_subscription(mock_view)
            response = decorated(request)
        
        # Debe redirigir a subscription_dashboard
        assert response.status_code == 302
    
    def test_blocks_ajax_without_subscription(self, request_factory, mock_view, disable_account_signals):
        """
        AJAX sin subscription debe retornar JSON error
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        with patch.object(org, 'get_subscription', return_value=None):
            request = request_factory.get(
                '/feature/',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            request.user = user
            request.user.organization = org
            
            decorated = require_active_subscription(mock_view)
            response = decorated(request)
        
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['success'] is False
        assert data['subscription_required'] is True


# ============================================================================
# TESTS DE require_plan_feature
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestRequirePlanFeatureDecorator:
    """
    Tests del decorador require_plan_feature - CRÍTICO para features premium
    """
    
    def test_allows_feature_in_plan(self, request_factory, mock_view, disable_account_signals):
        """Feature incluida en el plan debe permitir acceso"""
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock de subscription con feature
        mock_plan = Mock()
        mock_plan.get_feature_list.return_value = ['Feature A', 'Feature B']
        mock_plan.display_name = 'Basic Plan'
        
        mock_subscription = Mock()
        mock_subscription.plan = mock_plan
        
        with patch.object(org, 'get_subscription', return_value=mock_subscription):
            request = request_factory.get('/premium-feature/')
            request.user = user
            request.user.organization = org
            
            decorated = require_plan_feature('Feature A')(mock_view)
            response = decorated(request)
        
        assert response.status_code == 200
    
    def test_allows_superuser_any_feature(self, request_factory, mock_view):
        """Superuser debe tener acceso a cualquier feature"""
        user = SuperUserFactory()
        
        request = request_factory.get('/premium-feature/')
        request.user = user
        
        decorated = require_plan_feature('Any Feature')(mock_view)
        response = decorated(request)
        
        assert response.status_code == 200
    
    def test_blocks_feature_not_in_plan(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Feature NO incluida debe bloquear acceso
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # Mock de subscription sin la feature
        mock_plan = Mock()
        mock_plan.get_feature_list.return_value = ['Feature A']
        mock_plan.display_name = 'Basic Plan'
        
        mock_subscription = Mock()
        mock_subscription.plan = mock_plan
        
        with patch.object(org, 'get_subscription', return_value=mock_subscription):
            request = request_factory.get('/premium-feature/')
            request.user = user
            request.user.organization = org
            setattr(request, 'session', {})
            from django.contrib.messages.storage.fallback import FallbackStorage
            setattr(request, '_messages', FallbackStorage(request))
            
            decorated = require_plan_feature('Feature B')(mock_view)
            response = decorated(request)
        
        # Debe redirigir al dashboard de planes/suscripciones
        assert response.status_code == 302
        assert '/plans/dashboard/' in response.url or 'subscription_dashboard' in response.url
    
    def test_blocks_without_subscription(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Sin suscripción debe bloquear acceso a features
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        with patch.object(org, 'get_subscription', return_value=None):
            request = request_factory.get('/premium-feature/')
            request.user = user
            request.user.organization = org
            
            decorated = require_plan_feature('Any Feature')(mock_view)
            
            with pytest.raises(PermissionDenied):
                decorated(request)


# ============================================================================
# TESTS DE validate_organization_context
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestValidateOrganizationContextDecorator:
    """
    Tests del decorador validate_organization_context - CRÍTICO para seguridad
    Previene que usuarios accedan a recursos de otras organizaciones
    """
    
    def test_allows_superuser_any_organization(self, request_factory, mock_view):
        """Superuser debe poder operar en cualquier organización"""
        user = SuperUserFactory()
        
        request = request_factory.get('/org/123/')
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        response = decorated(request, org_id=123)
        
        assert response.status_code == 200
    
    def test_allows_user_own_organization(self, request_factory, mock_view, disable_account_signals):
        """Usuario debe poder operar en su propia organización"""
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        request = request_factory.get(f'/org/{org.id}/')
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        response = decorated(request, org_id=org.id)
        
        assert response.status_code == 200
    
    def test_blocks_access_to_other_organization(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: Usuario NO debe poder acceder a otra organización
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        user = UserFactory(organization=org1)
        
        request = request_factory.get(f'/org/{org2.id}/')
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request, org_id=org2.id)
    
    def test_blocks_ajax_access_to_other_organization(self, request_factory, mock_view, disable_account_signals):
        """
        CRÍTICO: AJAX request a otra org debe retornar JSON error
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        user = UserFactory(organization=org1)
        
        request = request_factory.get(
            f'/org/{org2.id}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        response = decorated(request, org_id=org2.id)
        
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['success'] is False
        assert data['organization_mismatch'] is True
    
    def test_allows_request_without_org_id(self, request_factory, mock_view, disable_account_signals):
        """Request sin org_id debe pasar (validación no aplica)"""
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        request = request_factory.get('/some-endpoint/')
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        response = decorated(request)
        
        assert response.status_code == 200
    
    def test_checks_org_id_in_get_params(self, request_factory, mock_view, disable_account_signals):
        """Debe validar org_id en parámetros GET"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        user = UserFactory(organization=org1)
        
        request = request_factory.get(f'/endpoint/?org_id={org2.id}')
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request)
    
    def test_checks_org_id_in_post_params(self, request_factory, mock_view, disable_account_signals):
        """Debe validar org_id en parámetros POST"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        user = UserFactory(organization=org1)
        
        request = request_factory.post('/endpoint/', {'org_id': org2.id})
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request)


# ============================================================================
# TESTS DE EDGE CASES Y SECURITY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDecoratorsSecurityEdgeCases:
    """
    Tests de casos extremos de seguridad - CRÍTICOS
    """
    
    def test_cannot_bypass_limit_with_ajax_header(self, request_factory, mock_view, disable_account_signals):
        """
        SECURITY: No se debe poder bypassear límites con header AJAX
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        with patch.object(org, 'can_add_user', return_value=False):
            with patch.object(org, 'can_add_user_detailed', return_value={
                'can_add': False,
                'total_users': 1,
                'active_users': 1,
                'inactive_users': 0,
                'has_inactive_users': False
            }):
                with patch.object(org, 'get_max_users', return_value=1):
                    request = request_factory.post(
                        '/users/create/',
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                    )
                    request.user = user
                    request.user.organization = org
                    
                    decorated = check_user_limit(mock_view)
                    response = decorated(request)
                    
                    # DEBE bloquear con código 400
                    assert response.status_code == 400
    
    def test_cannot_bypass_org_admin_with_is_org_admin_false(self, request_factory, mock_view, disable_account_signals):
        """
        SECURITY: Usuario con is_org_admin=False NO debe tener acceso
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org, is_org_admin=False)
        
        request = request_factory.get('/admin-only/')
        request.user = user
        
        decorated = require_org_admin(mock_view)
        
        with pytest.raises(PermissionDenied):
            decorated(request)
    
    def test_string_org_id_comparison_works(self, request_factory, mock_view, disable_account_signals):
        """
        BUG POTENCIAL: Comparación de org_id debe funcionar con strings
        """
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        
        # org_id viene como string desde URL
        request = request_factory.get(f'/org/{org.id}/')
        request.user = user
        
        decorated = validate_organization_context(mock_view)
        # Pasar org_id como string (como vendría de URL)
        response = decorated(request, org_id=str(org.id))
        
        # Debe pasar (comparación debe manejar string vs int)
        assert response.status_code == 200



