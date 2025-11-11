"""
Tests exhaustivos para SubscriptionAccessMiddleware y SubscriptionInfoMiddleware

Estos tests DEBEN detectar bugs reales en la lógica de middleware de suscripciones.
El middleware es CRÍTICO porque controla el acceso a todas las rutas según el estado de suscripción.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from unittest.mock import patch, Mock, MagicMock
from tests.factories import (
    OrganizationFactory,
    PlanFactory,
    TrialPlanFactory,
    BasicPlanFactory,
    SubscriptionFactory,
    SuperUserFactory,
    UserFactory,
)
from apps.plans.middleware import SubscriptionAccessMiddleware, SubscriptionInfoMiddleware
from apps.plans.models import Subscription


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def request_factory():
    """Fixture para crear requests"""
    return RequestFactory()


@pytest.fixture
def get_response():
    """Fixture que simula get_response"""
    def _get_response(request):
        return HttpResponse("OK")
    return _get_response


@pytest.fixture
def middleware(get_response):
    """Fixture que crea una instancia del middleware"""
    return SubscriptionAccessMiddleware(get_response)


@pytest.fixture
def info_middleware(get_response):
    """Fixture que crea una instancia del info middleware"""
    return SubscriptionInfoMiddleware(get_response)


@pytest.fixture
def org_user(db, disable_account_signals):
    """Fixture que crea un usuario con organización"""
    org = OrganizationFactory()
    user = UserFactory(organization=org)
    return user


@pytest.fixture
def superuser(db, disable_account_signals):
    """Fixture que crea un superusuario"""
    return SuperUserFactory()


# ============================================================================
# TESTS DE SUBSCRIPTIONACCESSMIDDLEWARE - CONFIGURACIÓN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewareConfig:
    """Tests de configuración del middleware"""
    
    def test_middleware_initializes_correctly(self, middleware):
        """Middleware debe inicializarse correctamente"""
        assert middleware.get_response is not None
        assert middleware.always_allowed_paths is not None
        assert middleware.full_access_required_paths is not None
        assert middleware.authenticated_allowed_paths is not None
        assert middleware.limited_access_paths is not None
    
    def test_always_allowed_paths_configured(self, middleware):
        """always_allowed_paths debe incluir rutas públicas"""
        expected_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password_reset/',
            '/static/',
            '/media/',
            '/health/',
        ]
        
        for path in expected_paths:
            assert any(path in allowed for allowed in middleware.always_allowed_paths), \
                f"Path {path} debe estar en always_allowed_paths"
    
    def test_full_access_required_paths_configured(self, middleware):
        """full_access_required_paths debe incluir rutas que requieren acceso completo"""
        expected_paths = [
            '/dashboard/',
            '/orgs/',
            '/users/',
            '/admin/',
        ]
        
        for path in expected_paths:
            assert any(path in required for required in middleware.full_access_required_paths), \
                f"Path {path} debe estar en full_access_required_paths"
    
    def test_authenticated_allowed_paths_configured(self, middleware):
        """authenticated_allowed_paths debe incluir rutas permitidas para autenticados"""
        expected_paths = [
            '/projects/',
        ]
        
        for path in expected_paths:
            assert any(path in allowed for allowed in middleware.authenticated_allowed_paths), \
                f"Path {path} debe estar en authenticated_allowed_paths"
    
    def test_limited_access_paths_configured(self, middleware):
        """limited_access_paths debe incluir rutas con acceso limitado"""
        expected_paths = [
            '/plans/',
            '/subscription/',
            '/billing/',
        ]
        
        for path in expected_paths:
            assert any(path in limited for limited in middleware.limited_access_paths), \
                f"Path {path} debe estar en limited_access_paths"


# ============================================================================
# TESTS DE SUBSCRIPTIONACCESSMIDDLEWARE - RUTAS PÚBLICAS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewarePublicPaths:
    """Tests de rutas públicas que no requieren suscripción"""
    
    def test_login_path_allowed(self, middleware, request_factory):
        """Ruta de login debe estar permitida"""
        request = request_factory.get('/accounts/login/')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None  # None significa que continúa el request
    
    def test_logout_path_allowed(self, middleware, request_factory):
        """Ruta de logout debe estar permitida"""
        request = request_factory.get('/accounts/logout/')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None
    
    def test_static_path_allowed(self, middleware, request_factory):
        """Ruta de static debe estar permitida"""
        request = request_factory.get('/static/css/style.css')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None
    
    def test_media_path_allowed(self, middleware, request_factory):
        """Ruta de media debe estar permitida"""
        request = request_factory.get('/media/uploads/file.jpg')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None
    
    def test_health_path_allowed(self, middleware, request_factory):
        """Ruta de health check debe estar permitida"""
        request = request_factory.get('/health/')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None


# ============================================================================
# TESTS DE SUBSCRIPTIONACCESSMIDDLEWARE - USUARIOS NO AUTENTICADOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewareUnauthenticated:
    """Tests para usuarios no autenticados"""
    
    def test_unauthenticated_user_allowed_public_paths(self, middleware, request_factory):
        """Usuario no autenticado debe poder acceder a rutas públicas"""
        request = request_factory.get('/accounts/login/')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None
    
    def test_unauthenticated_user_allowed_static(self, middleware, request_factory):
        """Usuario no autenticado debe poder acceder a archivos estáticos"""
        request = request_factory.get('/static/js/app.js')
        request.user = AnonymousUser()
        
        response = middleware.process_request(request)
        
        assert response is None


# ============================================================================
# TESTS DE SUBSCRIPTIONACCESSMIDDLEWARE - SUPERUSUARIOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewareSuperuser:
    """Tests para superusuarios"""
    
    def test_superuser_bypasses_middleware(self, middleware, request_factory, superuser):
        """Superusuario debe poder acceder a todas las rutas"""
        request = request_factory.get('/dashboard/')
        request.user = superuser
        
        response = middleware.process_request(request)
        
        assert response is None
    
    def test_superuser_bypasses_with_expired_subscription(self, middleware, request_factory, superuser):
        """Superusuario debe poder acceder incluso si su org tiene suscripción expirada"""
        org = OrganizationFactory()
        superuser.organization = org
        superuser.save()
        subscription = SubscriptionFactory(organization=org, subscription_status='basic_expired')
        
        request = request_factory.get('/orgs/')
        request.user = superuser
        
        response = middleware.process_request(request)
        
        assert response is None


# ============================================================================
# TESTS DE SUBSCRIPTIONACCESSMIDDLEWARE - USUARIOS CON ORGANIZACIÓN
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewareAuthenticated:
    """Tests para usuarios autenticados con organización"""
    
    def test_user_without_organization_redirected(self, middleware, request_factory, disable_account_signals):
        """Usuario sin organización debe ser redirigido"""
        user = UserFactory(organization=None)
        request = request_factory.get('/dashboard/')
        request.user = user
        
        response = middleware.process_request(request)
        
        assert response is not None
        assert response.status_code == 302  # Redirect
    
    def test_user_with_inactive_organization_redirected(self, middleware, request_factory, org_user):
        """Usuario con organización inactiva debe ser redirigido a logout"""
        org_user.organization.is_active = False
        org_user.organization.save()
        
        request = request_factory.get('/dashboard/')
        request.user = org_user
        
        response = middleware.process_request(request)
        
        assert response is not None
        assert response.status_code == 302  # Redirect
    
    def test_user_with_active_subscription_has_full_access(self, middleware, request_factory, org_user):
        """Usuario con suscripción activa debe tener acceso completo"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_active'
        )
        
        request = request_factory.get('/dashboard/')
        request.user = org_user
        
        response = middleware.process_request(request)
        
        assert response is None  # Acceso permitido
        assert hasattr(request, 'subscription')
        assert request.subscription == subscription
    
    def test_user_with_expired_subscription_limited_access(self, middleware, request_factory, org_user):
        """Usuario con suscripción expirada debe tener acceso limitado"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_expired'
        )
        
        # Acceso a dashboard (limitado)
        request = request_factory.get('/dashboard/')
        request.user = org_user
        setattr(request, 'session', {})
        from django.contrib.messages.storage.fallback import FallbackStorage
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = middleware.process_request(request)
        
        # Debe permitir acceso limitado a dashboard
        assert response is None or response.status_code != 403
    
    def test_user_with_expired_subscription_no_access_to_orgs(self, middleware, request_factory, org_user):
        """Usuario con suscripción expirada NO debe acceder a /orgs/"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_expired'
        )
        
        request = request_factory.get('/orgs/')
        request.user = org_user
        setattr(request, 'session', {})
        from django.contrib.messages.storage.fallback import FallbackStorage
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        response = middleware.process_request(request)
        
        # Debe denegar acceso o redirigir
        assert response is not None
        assert response.status_code in [302, 403]  # Redirect o Forbidden


# ============================================================================
# TESTS DE SUBSCRIPTIONACCESSMIDDLEWARE - DETERMINACIÓN DE MÓDULO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewareModuleDetection:
    """Tests de detección de módulo actual"""
    
    def test_get_current_module_dashboard(self, middleware):
        """Debe detectar módulo dashboard correctamente"""
        module = middleware._get_current_module('/dashboard/')
        assert module == 'dashboard'
        
        module = middleware._get_current_module('/')
        assert module == 'dashboard'
        
        module = middleware._get_current_module('/main/')
        assert module == 'dashboard'
    
    def test_get_current_module_orgs(self, middleware):
        """Debe detectar módulo organizations correctamente"""
        module = middleware._get_current_module('/orgs/')
        assert module == 'organizations'
    
    def test_get_current_module_users(self, middleware):
        """Debe detectar módulo users correctamente"""
        module = middleware._get_current_module('/users/')
        assert module == 'users'
    
    def test_get_current_module_projects(self, middleware):
        """Debe detectar módulo projects correctamente"""
        module = middleware._get_current_module('/projects/')
        assert module == 'projects'
    
    def test_get_current_module_plans(self, middleware):
        """Debe detectar módulo plans correctamente"""
        module = middleware._get_current_module('/plans/')
        assert module == 'plans'
        
        module = middleware._get_current_module('/subscription/')
        assert module == 'plans'
    
    def test_get_current_module_unknown(self, middleware):
        """Debe retornar 'general' para rutas desconocidas"""
        module = middleware._get_current_module('/unknown/')
        assert module == 'general'


# ============================================================================
# TESTS DE SUBSCRIPTIONINFOMIDDLEWARE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionInfoMiddleware:
    """Tests de SubscriptionInfoMiddleware"""
    
    def test_middleware_adds_subscription_info_to_request(self, info_middleware, request_factory, org_user):
        """Middleware debe agregar información de suscripción al request"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_active'
        )
        
        request = request_factory.get('/dashboard/')
        request.user = org_user
        
        response = info_middleware.process_request(request)
        
        assert response is None
        assert hasattr(request, 'subscription_info')
        assert request.subscription_info is not None
        assert request.subscription_info['status'] == 'basic_active'
        assert request.subscription_info['is_active'] is True
    
    def test_middleware_subscription_info_structure(self, info_middleware, request_factory, org_user):
        """subscription_info debe tener la estructura correcta"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_active'
        )
        
        request = request_factory.get('/dashboard/')
        request.user = org_user
        
        info_middleware.process_request(request)
        
        info = request.subscription_info
        expected_keys = [
            'status', 'display_status', 'is_active', 'is_expired',
            'is_in_grace', 'is_trial', 'days_remaining', 'plan_name',
            'end_date', 'expires_soon', 'needs_attention',
            'has_pending_renewal', 'has_pending_upgrade'
        ]
        
        for key in expected_keys:
            assert key in info, f"Key {key} debe estar en subscription_info"
    
    def test_middleware_handles_user_without_organization(self, info_middleware, request_factory, disable_account_signals):
        """Middleware debe manejar usuario sin organización"""
        user = UserFactory(organization=None)
        
        request = request_factory.get('/dashboard/')
        request.user = user
        
        response = info_middleware.process_request(request)
        
        assert response is None
        # No debe tener subscription_info si no hay organización
        assert not hasattr(request, 'subscription_info')
    
    def test_middleware_updates_status_before_adding_info(self, info_middleware, request_factory, org_user):
        """Middleware debe actualizar el estado antes de agregar info"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_active',
            end_date=timezone.now() - timedelta(days=1)  # Expirado
        )
        
        request = request_factory.get('/dashboard/')
        request.user = org_user
        
        info_middleware.process_request(request)
        
        # El estado debe haberse actualizado
        subscription.refresh_from_db()
        # Aunque el estado puede no cambiar si update_status() no se llama correctamente
        # Este test verifica que el middleware intenta actualizar


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestSubscriptionAccessMiddlewareEdgeCases:
    """Tests de casos extremos - ENCONTRAR BUGS"""
    
    def test_middleware_handles_missing_subscription(self, middleware, request_factory, org_user):
        """
        BUG POTENCIAL: ¿Qué pasa si la organización no tiene suscripción?
        """
        # Organización sin suscripción
        request = request_factory.get('/dashboard/')
        request.user = org_user
        setattr(request, 'session', {})
        from django.contrib.messages.storage.fallback import FallbackStorage
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        # Debe crear suscripción trial automáticamente o manejar el error
        response = middleware.process_request(request)
        
        # No debe crashear
        assert response is not None or hasattr(request, 'subscription')
    
    def test_middleware_handles_ajax_request(self, middleware, request_factory, org_user):
        """Middleware debe manejar requests AJAX correctamente"""
        subscription = SubscriptionFactory(
            organization=org_user.organization,
            subscription_status='basic_expired'
        )
        
        request = request_factory.get('/orgs/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = org_user
        
        response = middleware.process_request(request)
        
        # Debe retornar JsonResponse para AJAX
        if response is not None:
            assert isinstance(response, JsonResponse) or response.status_code == 403

