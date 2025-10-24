from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.db.models import Count, Q, Sum
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import SystemSettings

User = get_user_model()


class AdminDashboard:
    """Dashboard personalizado para el admin con estadísticas útiles."""
    
    def __init__(self, admin_site):
        self.admin_site = admin_site
    
    def get_stats(self):
        """Obtener estadísticas del sistema enfocadas en métricas administrativas útiles."""
        try:
            # Importar modelos aquí para evitar errores de importación circular
            from apps.orgs.models import Organization
            from apps.plans.models import Subscription, Plan, Payment, UpgradeRequest, RenewalRequest
            from django.db.models import Sum, Count, Q
            from decimal import Decimal
            from datetime import datetime, timedelta
            
            # === MÉTRICAS DE USUARIOS ===
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            staff_users = User.objects.filter(is_staff=True).count()
            org_admins = User.objects.filter(is_org_admin=True).count()
            
            # === MÉTRICAS DE ORGANIZACIONES ===
            total_orgs = Organization.objects.count()
            active_orgs = Organization.objects.filter(is_active=True).count()
            
            # === MÉTRICAS FINANCIERAS ===
            # Ingresos totales (suma de todos los pagos completados)
            total_revenue = Payment.objects.filter(
                status='completed',
                payment_type='subscription'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Ingresos del mes actual
            current_month = timezone.now().replace(day=1)
            monthly_revenue = Payment.objects.filter(
                status='completed',
                payment_type='subscription',
                created_at__gte=current_month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Ingresos por mes (últimos 6 meses)
            monthly_breakdown = []
            for i in range(6):
                month_start = (current_month - timedelta(days=30*i)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_revenue = Payment.objects.filter(
                    status='completed',
                    payment_type='subscription',
                    created_at__gte=month_start,
                    created_at__lte=month_end
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                monthly_breakdown.append({
                    'month_name': month_start.strftime('%b %Y'),
                    'amount': f"{month_revenue:,.0f}",
                    'is_current': i == 0
                })
            
            # Solicitudes de upgrade detalladas
            upgrade_requests = []
            for request in UpgradeRequest.objects.filter(status='pending').order_by('-created_at')[:10]:
                upgrade_requests.append({
                    'id': request.id,
                    'organization_name': request.organization.name,
                    'current_plan': request.current_plan.display_name,
                    'requested_plan': request.requested_plan.display_name,
                    'amount': f"{request.amount:,.0f}",
                    'status': request.status,
                    'created_at': request.created_at
                })
            
            # Solicitudes de renovación detalladas
            renewal_requests = []
            for r in RenewalRequest.objects.filter(status='pending').order_by('-created_at')[:10]:
                renewal_requests.append({
                    'id': r.id,
                    'organization_name': r.organization.name,
                    'plan_name': r.subscription.plan.display_name,
                    'amount': f"{r.renewal_amount:,.0f}",
                    'days': r.renewal_days,
                    'status': r.status,
                    'created_at': r.created_at
                })
            
            # === MÉTRICAS DE SUSCRIPCIONES ===
            active_subscriptions = Subscription.objects.filter(
                subscription_status__in=['trial_active', 'basic_active']
            ).count()
            
            trial_subscriptions = Subscription.objects.filter(
                subscription_status='trial_active'
            ).count()
            
            basic_subscriptions = Subscription.objects.filter(
                subscription_status='basic_active'
            ).count()
            
            grace_subscriptions = Subscription.objects.filter(
                subscription_status='basic_grace'
            ).count()
            
            expired_subscriptions = Subscription.objects.filter(
                subscription_status__in=['trial_expired', 'basic_expired']
            ).count()
            
            # === NOTIFICACIONES Y ALERTAS ===
            # Solicitudes de upgrade pendientes
            pending_upgrades = UpgradeRequest.objects.filter(status='pending').count()
            # Solicitudes de renovación pendientes
            pending_renewals = RenewalRequest.objects.filter(status='pending').count()
            
            # Suscripciones que expiran en los próximos 7 días
            week_from_now = timezone.now() + timedelta(days=7)
            expiring_soon = Subscription.objects.filter(
                end_date__lte=week_from_now,
                subscription_status__in=['trial_active', 'basic_active']
            ).count()
            
            # Organizaciones en período de gracia
            in_grace_period = Subscription.objects.filter(
                subscription_status='basic_grace'
            ).count()
            

            
            return {
                # Métricas principales para el admin
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'staff': staff_users,
                    'org_admins': org_admins,
                },
                'organizations': {
                    'total': total_orgs,
                    'active': active_orgs,
                },
                'financial': {
                    'total_revenue': f"{total_revenue:,.0f}",
                    'monthly_revenue': f"{monthly_revenue:,.0f}",
                    'current_month_name': current_month.strftime('%B %Y'),
                    'monthly_breakdown': monthly_breakdown,
                },
                'upgrade_requests': upgrade_requests,
                'renewal_requests': renewal_requests,
                'subscriptions': {
                    'active': active_subscriptions,
                    'trial': trial_subscriptions,
                    'basic': basic_subscriptions,
                    'grace': grace_subscriptions,
                    'expired': expired_subscriptions,
                },
                'notifications': {
                    'pending_upgrades': pending_upgrades,
                    'pending_renewals': pending_renewals,
                    'expiring_soon': expiring_soon,
                    'in_grace_period': in_grace_period,
                },
            }
        except Exception as e:
            # En caso de error, devolver estadísticas vacías
            return {
                'users': {'total': 0, 'active': 0, 'staff': 0, 'org_admins': 0},
                'organizations': {'total': 0, 'active': 0},
                'financial': {'total_revenue': '0', 'monthly_revenue': '0', 'current_month_name': 'N/A', 'monthly_breakdown': []},
                'upgrade_requests': [],
                'renewal_requests': [],
                'subscriptions': {'active': 0, 'trial': 0, 'basic': 0, 'grace': 0, 'expired': 0},
                'notifications': {'pending_upgrades': 0, 'pending_renewals': 0, 'expiring_soon': 0, 'in_grace_period': 0},
                'error': str(e)
            }


# Personalizar el admin por defecto
admin.site.site_header = "🏗️ ARC Manager - Panel de Administración"
admin.site.site_title = "ARC Manager Admin"
admin.site.index_title = "Panel de Control - Gestión Integral de Proyectos Arquitectónicos"


# Función para agregar el dashboard al template admin/index.html
def add_dashboard_to_admin_index():
    """Agregar información del dashboard al contexto del admin."""
    original_index_view = admin.site.index
    
    def enhanced_index_view(request, extra_context=None):
        dashboard = AdminDashboard(admin.site)
        stats = dashboard.get_stats()
        
        extra_context = extra_context or {}
        extra_context.update({
            'dashboard_stats': stats,
            'show_dashboard': True,
        })
        
        return original_index_view(request, extra_context)
    
    admin.site.index = enhanced_index_view


# Vista para el dashboard financiero
def financial_dashboard_view(request):
    """Vista para el dashboard financiero detallado."""
    dashboard = AdminDashboard(admin.site)
    stats = dashboard.get_stats()
    
    return TemplateResponse(request, 'admin/financial_dashboard.html', {
        'dashboard_stats': stats,
        'title': 'Dashboard Financiero',
        'site_title': admin.site.site_title,
        'site_header': admin.site.site_header,
    })


# Aplicar la mejora al cargar el módulo
add_dashboard_to_admin_index()


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Admin para las configuraciones globales del sistema.
    Solo permite editar (no crear ni eliminar) la instancia única.
    TODOS los cambios se aplican automáticamente al guardar.
    """
    
    def has_add_permission(self, request):
        """No permitir crear nuevas configuraciones (solo una instancia)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirigir directamente al formulario de edición"""
        settings = SystemSettings.load()
        return self.change_view(request, str(settings.pk), '', extra_context)
    
    fieldsets = (
        ('👥 Límites de Usuarios', {
            'fields': (
                'default_max_users',
                'max_users_trial',
                'max_users_basic',
            ),
            'description': 'Configure los límites de usuarios para cada tipo de plan.'
        }),
        ('💾 Límites de Almacenamiento', {
            'fields': (
                'default_storage_gb',
                'storage_trial_gb',
                'storage_basic_gb',
            ),
            'description': 'Configure los límites de almacenamiento en gigabytes para cada plan.'
        }),
        ('📁 Límites de Archivos', {
            'fields': (
                'max_file_size_mb',
            ),
            'description': 'Configure el tamaño máximo permitido por archivo individual. La aplicación solo permite subir 1 archivo a la vez.'
        }),
        ('⚡ Configuración de Caché', {
            'fields': (
                'cache_timeout_seconds',
                'storage_cache_timeout',
            ),
            'description': 'Configure los tiempos de caché del sistema.',
            'classes': ('collapse',)
        }),
        ('🔒 Sesiones y Seguridad', {
            'fields': (
                'session_timeout_minutes',
            ),
            'description': 'Configure parámetros de sesión.',
            'classes': ('collapse',)
        }),
        ('🚦 Rate Limiting - Control de Carga', {
            'fields': (
                'upload_requests_per_minute',
                'upload_requests_per_hour',
                'upload_size_per_hour_mb',
            ),
            'description': 'Configure límites de velocidad para evitar sobrecarga del servidor.',
            'classes': ('collapse',)
        }),
        ('💳 Planes y Facturación', {
            'fields': (
                'trial_duration_days',
                'billing_cycle_days',
                'grace_period_days',
            ),
            'description': 'Configure parámetros por defecto de planes y facturación.'
        }),
        ('🔔 Notificaciones y Alertas', {
            'fields': (
                'enable_email_notifications',
                'low_storage_warning_percentage',
            ),
            'description': 'Configure alertas y notificaciones del sistema.',
            'classes': ('collapse',)
        }),
        ('🔧 Modo Mantenimiento', {
            'fields': (
                'maintenance_mode',
                'maintenance_message',
            ),
            'description': 'Active el modo mantenimiento cuando necesite realizar actualizaciones. Solo staff y superusuarios podrán acceder.',
            'classes': ('collapse',)
        }),
        ('📧 Información de Contacto', {
            'fields': (
                'company_name',
                'support_email',
            ),
            'description': 'Configure información de contacto y soporte.',
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': (
                'updated_at',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('updated_at',)
    
    def save_model(self, request, obj, form, change):
        """Guardar quién actualizó la configuración"""
        obj.updated_by = f"{request.user.email} (ID: {request.user.pk})"
        super().save_model(request, obj, form, change)
        
        # Mensaje de éxito simple - los signals se encargan de sincronizar automáticamente
        self.message_user(
            request,
            "✅ Configuración actualizada exitosamente. Los cambios se aplicaron automáticamente.",
            level='success'
        )