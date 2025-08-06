from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import Organization, Client
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.db import models

# --- Recursos para Import/Export ---

class OrganizationResource(resources.ModelResource):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'is_active', 'created_at', 'subscription__plan__name', 'subscription__end_date')
        export_order = fields

class ClientResource(resources.ModelResource):
    class Meta:
        model = Client
        fields = ('id', 'name', 'organization__name', 'email', 'phone_number', 'is_active')
        export_order = fields

@admin.register(Organization)
class OrganizationAdmin(ImportExportModelAdmin):
    resource_class = OrganizationResource
    list_display = ['name', 'is_active', 'user_count', 'get_subscription_status', 'get_subscription_link', 'created_at']
    list_filter = ['is_active', 'created_at', 'subscription__plan__display_name', 'subscription__subscription_status']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'user_count', 'get_subscription_status', 'get_subscription_link']
    
    actions = ['activate_organizations', 'deactivate_organizations']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Suscripción', {
            'fields': ('get_subscription_status', 'get_subscription_link'),
            'description': '📝 Para gestionar planes y suscripciones, usa el módulo "Suscripciones" del admin.',
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('user_count',),
            'classes': ('collapse',)
        }),
        ('Información del sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimizar la carga de datos con prefetch y anotaciones."""
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('subscription__plan')
        queryset = queryset.annotate(user_count_admin=models.Count('users'))
        return queryset

    def user_count(self, obj):
        """Muestra el total de usuarios desde la anotación."""
        return f"{obj.user_count_admin} usuarios"
    user_count.short_description = 'Usuarios'
    user_count.admin_order_field = 'user_count_admin' # Permite ordenar por esta columna

    def get_subscription_status(self, obj):
        """Muestra el estado de la suscripción de forma simple y visual."""
        if hasattr(obj, 'subscription') and obj.subscription:
            subscription = obj.subscription
            plan = subscription.plan
            status_text = subscription.get_subscription_status_display()
            
            color = 'black'
            if subscription.is_active:
                color = 'green'
                if 'trial' in subscription.subscription_status:
                    color = '#E67E22'
            elif subscription.is_in_grace_period:
                color = '#F39C12'
            elif subscription.is_expired:
                color = '#E74C3C'

            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span><br>'
                '<small style="color: #555;">{} - {} días restantes</small>',
                color,
                status_text,
                plan.display_name,
                subscription.days_remaining
            )
        return format_html('<span style="color: #C0392B; font-weight: bold;">Sin suscripción</span>')
    get_subscription_status.short_description = 'Estado de Suscripción'
    
    def get_subscription_link(self, obj):
        """Proporciona un enlace para gestionar la suscripción."""
        if hasattr(obj, 'subscription') and obj.subscription:
            subscription_url = reverse('admin:plans_subscription_change', args=[obj.subscription.pk])
            return format_html('<a href="{}" class="button">📝 Gestionar suscripción</a>', subscription_url)
        else:
            add_subscription_url = reverse('admin:plans_subscription_add') + f'?organization={obj.pk}'
            return format_html('<a href="{}" class="button">➕ Crear suscripción</a>', add_subscription_url)
    get_subscription_link.short_description = 'Gestión'
    
    def activate_organizations(self, request, queryset):
        """Activar organizaciones seleccionadas"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✅ Se activaron {updated} organizaciones correctamente.", messages.SUCCESS)
    activate_organizations.short_description = "✅ Activar organizaciones"
    
    def deactivate_organizations(self, request, queryset):
        """Desactivar organizaciones seleccionadas"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"❌ Se desactivaron {updated} organizaciones correctamente.", messages.SUCCESS)
    deactivate_organizations.short_description = "❌ Desactivar organizaciones"

@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    list_display = ('name', 'organization', 'email', 'phone_number', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization__name')
    search_fields = ('name', 'email', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['organization']

    fieldsets = (
        ('Información del Cliente', {
            'fields': ('organization', 'name', 'email', 'phone_number', 'address', 'is_active')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimizar la carga de la organización."""
        queryset = super().get_queryset(request)
        return queryset.select_related('organization')
