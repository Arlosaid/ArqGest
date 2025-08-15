# apps/plans/views.py (actualizado)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
import logging

from .models import Plan, Subscription, UpgradeRequest
from apps.orgs.models import Organization
from .services import SubscriptionService


# El logger se configurará localmente en cada función para evitar problemas de inicialización


# Mixins para verificación de permisos
class OrgAdminRequiredMixin(UserPassesTestMixin):
    """Mixin para requerir permisos de org_admin"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and hasattr(user, 'is_org_admin') and user.is_org_admin
    
    def handle_no_permission(self):
        raise PermissionDenied("Necesitas permisos de administrador de organización.")


# Vistas para usuarios autenticados
class SubscriptionDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard de suscripción simplificado.
    La vista solo obtiene los objetos principales, y la lógica de presentación
    se delega completamente a la plantilla.
    """
    template_name = 'plans/subscription_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        organization = getattr(user, 'organization', None)
        
        if not organization:
            context['no_organization'] = True
            return context
        
        # Usar el servicio simplificado para obtener o crear la suscripción
        subscription = Subscription.objects.filter(organization=organization).first()
        if not subscription:
            trial_plan = Plan.get_trial_plan()
            if trial_plan:
                 subscription = Subscription.objects.create(
                    organization=organization,
                    plan=trial_plan
                )
            else:
                # Fallback por si no hay plan de prueba
                context['error'] = "No se pudo inicializar la suscripción. No hay un plan de prueba configurado."
                return context

        # Actualiza el estado al cargar la página
        subscription.update_status()

        context['subscription'] = subscription
        context['organization'] = organization
        context['is_org_admin'] = user.is_org_admin
        
        # Pasar las solicitudes de upgrade directamente a la plantilla
        context['pending_request'] = UpgradeRequest.objects.filter(
            organization=organization,
            status='pending'
        ).first()
        
        # Pasar los planes disponibles para que la plantilla decida si mostrarlos
        context['available_plans'] = Plan.objects.filter(
            is_active=True,
            price__gt=subscription.plan.price
        ).order_by('price')

        # Pasar el historial de pagos directamente
        context['payment_history'] = subscription.get_payment_history(limit=5)

        # Datos de contacto de soporte desde settings
        from django.conf import settings
        context['support_phone'] = getattr(settings, 'SUPPORT_PHONE', '55 1234 5678')
        context['support_email'] = getattr(settings, 'SUPPORT_EMAIL', 'soporte@tuempresa.com')
        
        return context


# Las Vistas de Superusuario y API innecesarias han sido eliminadas para el MVP.


class RequestUpgradeView(LoginRequiredMixin, OrgAdminRequiredMixin, TemplateView):
    """Vista simplificada para que los usuarios soliciten una actualización de plan."""
    template_name = 'plans/request_upgrade.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.user.organization
        subscription = get_object_or_404(Subscription, organization=organization)

        context['subscription'] = subscription
        context['has_pending_request'] = UpgradeRequest.objects.filter(
            organization=organization,
            status='pending'
        ).exists()
        
        if not context['has_pending_request']:
            context['available_plans'] = Plan.objects.filter(
                is_active=True,
                price__gt=subscription.plan.price
            ).order_by('price')
            
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesa una solicitud de actualización de plan de forma simple y directa."""
        organization = request.user.organization
        subscription = get_object_or_404(Subscription, organization=organization)
        requested_plan_id = request.POST.get('requested_plan')
        
        # 1. Verificar que no haya una solicitud pendiente
        if UpgradeRequest.objects.filter(organization=organization, status='pending').exists():
            messages.warning(request, "Ya tienes una solicitud de actualización pendiente.")
            return redirect('plans:subscription_dashboard')

        # 2. Validar el plan solicitado
        if not requested_plan_id:
            messages.error(request, "Debes seleccionar un plan.")
            return redirect('plans:request_upgrade')
            
        try:
            requested_plan = Plan.objects.get(id=requested_plan_id, is_active=True)
        except Plan.DoesNotExist:
            messages.error(request, "El plan seleccionado no es válido.")
            return redirect('plans:request_upgrade')
            
        # 3. Validar que sea una actualización a un plan superior
        if requested_plan.price <= subscription.plan.price:
            messages.error(request, "Solo puedes actualizar a un plan de mayor valor.")
            return redirect('plans:request_upgrade')

        # 4. Crear la solicitud
        try:
            with transaction.atomic():
                UpgradeRequest.objects.create(
                    organization=organization,
                    current_plan=subscription.plan,
                    requested_plan=requested_plan,
                    amount=requested_plan.price
                )
                
            messages.success(
                request, 
                f"Tu solicitud de actualización a {requested_plan.display_name} ha sido enviada. "
                "Recibirás instrucciones de pago una vez que sea aprobada."
            )
            return redirect('plans:subscription_dashboard')
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error al crear solicitud de actualización: {e}", exc_info=True)
            messages.error(request, "Ocurrió un error al procesar tu solicitud. Por favor, contacta a soporte.")
            return redirect('plans:request_upgrade')


class SubscriptionInfoAPIView(LoginRequiredMixin, View):
    """Vista API para obtener información de suscripción para notificaciones automáticas"""
    
    def get(self, request):
        """Devuelve información de suscripción en formato JSON"""
        try:
            # Verificar que el usuario tenga organización
            if not hasattr(request.user, 'organization') or not request.user.organization:
                return JsonResponse({'error': 'Usuario sin organización'}, status=400)
            
            # Obtener suscripción
            subscription = SubscriptionService.get_subscription_or_create(request.user.organization)
            if not subscription:
                return JsonResponse({'error': 'No se pudo obtener la suscripción'}, status=500)
            
            # Obtener estadísticas de uso
            organization = request.user.organization
            current_users = organization.users.filter(is_active=True, is_superuser=False).count()
            current_projects = organization.projects.count() if hasattr(organization, 'projects') else 0
            
            # Preparar respuesta
            response_data = {
                'status': subscription.subscription_status,
                'display_status': subscription.get_subscription_status_display(),
                'is_active': subscription.is_active,
                'is_expired': subscription.is_expired,
                'is_in_grace': subscription.is_in_grace_period,
                'is_trial': subscription.plan.is_trial,
                'days_remaining': subscription.days_remaining,
                'plan_name': subscription.plan.display_name,
                'expires_soon': subscription.days_remaining <= 7 and subscription.days_remaining > 0,
                'needs_attention': subscription.is_expired or subscription.is_in_grace_period,
                
                # Información de uso
                'user_usage': current_users,
                'user_limit': subscription.plan.max_users,
                'user_percentage': subscription.plan.get_usage_percentage(current_users, 'users'),
                
                # Proyectos (si está disponible)
                'project_usage': current_projects,
                'project_limit': 999,  # Sin límite por ahora, se puede configurar después
                'project_percentage': 0,
                
                # Fechas importantes
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error en SubscriptionInfoAPIView: {e}", exc_info=True)
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)