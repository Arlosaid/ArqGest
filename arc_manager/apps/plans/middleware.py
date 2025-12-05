from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied
from django.conf import settings
import logging

from .services import SubscriptionService
from core.structured_logging import log_warning

logger = logging.getLogger(__name__)

class SubscriptionAccessMiddleware(MiddlewareMixin):
    """
    Middleware para verificar automáticamente el acceso según el estado de suscripción
    
    MVP: Bloquea acceso a módulos no permitidos según el estado de suscripción
    Configurable por settings y rutas
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rutas que siempre están permitidas (sin verificación de suscripción)
        self.always_allowed_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password_reset/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/plans/cron/renewal-reminders/',  # Endpoint para cron externo
            '/health/',  # Health check endpoint
        ]
        
        # Rutas que requieren acceso completo
        self.full_access_required_paths = [
            '/dashboard/',
            '/orgs/',
            '/users/',
            '/reports/',   # Para el futuro
            '/admin/',
        ]
        
        # Rutas que siempre están permitidas para usuarios autenticados (sin verificación de suscripción)
        self.authenticated_allowed_paths = [
            '/projects/',  # Los usuarios pueden acceder a proyectos siempre
        ]
        
        # Rutas que pueden funcionar con acceso limitado
        self.limited_access_paths = [
            '/plans/',
            '/subscription/',
            '/billing/',
        ]
        
        # Configuración desde settings
        self.enabled = getattr(settings, 'SUBSCRIPTION_ACCESS_MIDDLEWARE_ENABLED', True)
        self.redirect_url = getattr(settings, 'SUBSCRIPTION_EXPIRED_REDIRECT_URL', 'plans:subscription_dashboard')
        
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Procesa cada request para verificar permisos de suscripción
        """
        # Bypass middleware en modo testing
        if getattr(settings, 'TESTING', False):
            return None
            
        # Verificar si el middleware está habilitado
        if not self.enabled:
            return None
        
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return None
        
        # Verificar si es superuser (siempre permitido)
        if request.user.is_superuser:
            return None
        
        # Verificar si la ruta está en las permitidas siempre
        if self._is_always_allowed(request.path):
            return None
        
        # Verificar si la ruta está permitida para usuarios autenticados
        if self._is_authenticated_allowed(request.path):
            return None
        
        # Verificar si el usuario tiene organización
        if not hasattr(request.user, 'organization') or not request.user.organization:
            # Usuario sin organización - redirigir a configuración
            if not request.path.startswith('/accounts/'):
                messages.warning(request, 'Necesitas estar asociado a una organización para acceder a esta sección.')
                return redirect('orgs:my_organization')
            return None
        
        # Verificar si la organización está activa
        if not request.user.organization.is_active:
            messages.error(request, 'Tu organización ha sido desactivada. Por favor contacta con soporte.')
            return redirect('accounts:logout')
        
        # Obtener suscripción
        subscription = SubscriptionService.get_subscription_or_create(request.user.organization)
        if not subscription:
            # Error obteniendo suscripción
            messages.error(request, 'Error verificando tu suscripción. Por favor contacta al soporte.')
            return redirect(self.redirect_url)
        
        # Determinar el módulo actual
        current_module = self._get_current_module(request.path)
        
        # Sincronizar estado antes de validar acceso
        try:
            if hasattr(subscription, 'update_status'):
                if subscription.update_status():
                    subscription.refresh_from_db()
        except Exception as e:
            log_warning(
                event="subscription_status_update_failed",
                message="Error al sincronizar estado de suscripción",
                error_message=str(e),
                subscription_id=subscription.id if subscription else None,
                organization_id=request.user.organization.id,
                user_id=request.user.id,
                logger_name='apps.plans'
            )

        # Verificar permisos de acceso
        access_result = SubscriptionService.check_access_permissions(subscription, current_module)
        
        if not access_result.get('has_access', False):
            return self._handle_access_denied(request, access_result)
        
        # Agregar información de suscripción al request para uso posterior
        request.subscription = subscription
        request.subscription_access = access_result
        
        return None
    
    def _is_always_allowed(self, path):
        """Verifica si la ruta está siempre permitida"""
        for allowed_path in self.always_allowed_paths:
            if path.startswith(allowed_path):
                return True
        return False
    
    def _is_authenticated_allowed(self, path):
        """Verifica si la ruta está permitida para usuarios autenticados"""
        for allowed_path in self.authenticated_allowed_paths:
            if path.startswith(allowed_path):
                return True
        return False
    
    def _get_current_module(self, path):
        """Determina el módulo actual basado en la ruta"""
        # Tratar la raíz y /main/ como dashboard para permitir acceso limitado cuando expira
        if path == '/' or path.startswith('/main/') or path.startswith('/dashboard/'):
            return 'dashboard'
        elif path.startswith('/orgs/'):
            return 'organizations'
        elif path.startswith('/users/'):
            return 'users'
        elif path.startswith('/projects/'):
            return 'projects'
        elif path.startswith('/reports/'):
            return 'reports'
        elif path.startswith('/plans/') or path.startswith('/subscription/'):
            return 'plans'
        elif path.startswith('/billing/'):
            return 'billing'
        else:
            return 'general'
    
    def _handle_access_denied(self, request, access_result):
        """Maneja el acceso denegado según el tipo de request"""
        
        # Verificar si es un request AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': access_result.get('message', 'Acceso denegado'),
                'access_level': access_result.get('access_level', 'none'),
                'redirect_url': reverse(self.redirect_url) if access_result.get('redirect_to') else None
            }, status=403)
        
        # Request normal
        message = access_result.get('message', 'Acceso denegado')

        # Si el usuario NO es admin de organización, mostrar 403 simple y claro
        is_org_admin = getattr(request.user, 'is_org_admin', False)
        if not is_org_admin:
            # Mostrar 403 con mensaje y CTA a proyectos
            context = {
                'custom_message': message or 'Tu suscripción está expirada. Contacta a tu administrador.',
                'show_projects_link': True,
            }
            return render(request, '403.html', context=context, status=403)

        # Para administradores de organización, mantener flujo actual con mensajes y redirección
        if access_result.get('access_level') == 'limited':
            messages.warning(request, message)
        else:
            messages.error(request, message)
        redirect_to = access_result.get('redirect_to', self.redirect_url)
        return redirect(redirect_to)


class SubscriptionInfoMiddleware(MiddlewareMixin):
    """
    Middleware ligero para agregar información de suscripción al contexto
    Útil para mostrar alertas o información en el template
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Agrega información de suscripción al request"""
        
        # Bypass middleware en modo testing
        if getattr(settings, 'TESTING', False):
            return None
        
        # Solo para usuarios autenticados con organización
        if (request.user.is_authenticated and 
            hasattr(request.user, 'organization') and 
            request.user.organization):
            
            subscription = SubscriptionService.get_subscription_or_create(request.user.organization)
            if subscription:
                # Asegurar estado actualizado
                try:
                    if hasattr(subscription, 'update_status'):
                        if subscription.update_status():
                            subscription.refresh_from_db()
                except Exception as e:
                    log_warning(
                        event="subscription_info_status_update_failed",
                        message="Error al actualizar estado de suscripción en info middleware",
                        error_message=str(e),
                        subscription_id=subscription.id if subscription else None,
                        organization_id=request.user.organization.id,
                        user_id=request.user.id,
                        logger_name='apps.plans'
                    )

                # Verificar si hay solicitudes pendientes (CON CACHE para evitar queries en cada request)
                from django.core.cache import cache
                org_id = request.user.organization.id
                pending_cache_key = f"org_pending_requests:{org_id}"
                pending_data = cache.get(pending_cache_key)
                
                if pending_data is None:
                    from .models import RenewalRequest, UpgradeRequest
                    has_pending_renewal = RenewalRequest.objects.filter(
                        organization=request.user.organization,
                        status='pending'
                    ).exists()
                    has_pending_upgrade = UpgradeRequest.objects.filter(
                        organization=request.user.organization,
                        status='pending'
                    ).exists()
                    pending_data = {
                        'renewal': has_pending_renewal,
                        'upgrade': has_pending_upgrade
                    }
                    # Cache por 60 segundos - balance entre rendimiento y frescura de datos
                    cache.set(pending_cache_key, pending_data, 60)
                else:
                    has_pending_renewal = pending_data['renewal']
                    has_pending_upgrade = pending_data['upgrade']
                
                # Calcular fecha de inicio de la nueva suscripción (si hay renovación o upgrade pendiente)
                from django.utils import timezone
                from datetime import timedelta
                new_subscription_start = None
                new_subscription_end = None
                
                if (has_pending_renewal or has_pending_upgrade) and subscription.end_date:
                    # La nueva suscripción comienza cuando termina la actual
                    now = timezone.now()
                    base_date = max(now, subscription.end_date)
                    new_subscription_start = base_date
                    # Para upgrade, intentar obtener el plan solicitado
                    billing_days = subscription.plan.billing_cycle_days
                    if has_pending_upgrade:
                        try:
                            pending_upgrade = UpgradeRequest.objects.filter(
                                organization=request.user.organization,
                                status='pending'
                            ).first()
                            if pending_upgrade and pending_upgrade.requested_plan:
                                billing_days = pending_upgrade.requested_plan.billing_cycle_days
                        except Exception:
                            pass
                    new_subscription_end = base_date + timedelta(days=billing_days)
                
                # Calcular expires_soon según tipo de plan:
                # - Trial (gratuito): banner aparece 2 días antes (days_remaining <= 2)
                # - Plan Básico: banner aparece el último día (days_remaining <= 1)
                # IMPORTANTE: expires_soon debe ser False si ya está expirada (is_expired)
                # para que se muestre el banner rojo de expirada en lugar del amarillo
                is_trial = subscription.plan.is_trial
                is_expired = subscription.is_expired
                days_remaining = subscription.days_remaining
                if is_expired:
                    # Si ya expiró, no debe mostrar "vence pronto" sino "expirada"
                    expires_soon = False
                elif is_trial:
                    expires_soon = days_remaining <= 2 and days_remaining >= 0
                else:
                    expires_soon = days_remaining <= 1 and days_remaining >= 0
                
                # Agregar información útil al request
                request.subscription_info = {
                    'status': subscription.subscription_status,
                    'display_status': subscription.get_subscription_status_display(),
                    'is_active': subscription.is_active,
                    'is_expired': is_expired,
                    'is_in_grace': subscription.is_in_grace_period,
                    'is_trial': is_trial,
                    'days_remaining': days_remaining,
                    'plan_name': subscription.plan.display_name,
                    'end_date': subscription.end_date,
                    'expires_soon': expires_soon,
                    'needs_attention': is_expired or subscription.is_in_grace_period,
                    'has_pending_renewal': has_pending_renewal,
                    'has_pending_upgrade': has_pending_upgrade,
                    'new_subscription_start': new_subscription_start,
                    'new_subscription_end': new_subscription_end,
                }
        
        return None


def subscription_required(allowed_statuses=None, redirect_url=None):
    """
    Decorador para vistas que requieren suscripción específica
    
    Uso:
    @subscription_required(allowed_statuses=['trial_active', 'basic_active'])
    def my_view(request):
        ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not hasattr(request.user, 'organization') or not request.user.organization:
                messages.warning(request, 'Necesitas estar asociado a una organización.')
                return redirect('orgs:my_organization')
            
            subscription = SubscriptionService.get_subscription_or_create(request.user.organization)
            if not subscription:
                messages.error(request, 'Error verificando tu suscripción.')
                return redirect(redirect_url or 'plans:subscription_dashboard')
            
            # Verificar estado específico si se requiere
            if allowed_statuses and subscription.subscription_status not in allowed_statuses:
                messages.error(request, 'Tu suscripción no permite acceder a esta función.')
                return redirect(redirect_url or 'plans:subscription_dashboard')
            
            # Verificar acceso general
            access_result = SubscriptionService.check_access_permissions(subscription)
            if not access_result.get('has_access', False):
                message = access_result.get('message', 'Acceso denegado')
                messages.error(request, message)
                return redirect(redirect_url or 'plans:subscription_dashboard')
            
            # Agregar subscription al request para uso en la vista
            request.subscription = subscription
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def full_access_required(view_func):
    """
    Decorador para vistas que requieren acceso completo (no expirado)
    
    Uso:
    @full_access_required
    def my_view(request):
        ...
    """
    return subscription_required(allowed_statuses=['trial_active', 'basic_active', 'basic_grace'])(view_func)


def trial_or_paid_required(view_func):
    """
    Decorador para vistas que requieren trial activo o plan de pago
    
    Uso:
    @trial_or_paid_required
    def my_view(request):
        ...
    """
    return subscription_required(allowed_statuses=['trial_active', 'basic_active'])(view_func)


def basic_plan_required(view_func):
    """
    Decorador para vistas que requieren plan básico específicamente
    
    Uso:
    @basic_plan_required
    def my_view(request):
        ...
    """
    return subscription_required(allowed_statuses=['basic_active', 'basic_grace'])(view_func)


# Utilidades para templates
def get_subscription_context(request):
    """
    Función auxiliar para obtener contexto de suscripción en templates
    """
    if not hasattr(request, 'subscription'):
        return {}
    
    subscription = request.subscription
    
    return {
        'subscription': subscription,
        'subscription_summary': subscription.get_subscription_summary(),
        'subscription_alerts': SubscriptionService._get_subscription_alerts(subscription),
        'subscription_actions': SubscriptionService._get_available_actions(subscription),
        'usage_stats': SubscriptionService._get_usage_stats(subscription),
    } 