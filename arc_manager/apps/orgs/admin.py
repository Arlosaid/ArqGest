from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import ModelForm
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

class OrganizationAdminForm(ModelForm):
    """Form personalizado para validar cambios en extra_storage_gb"""
    
    class Meta:
        model = Organization
        fields = '__all__'
    
    def clean_extra_storage_gb(self):
        """Validar que el almacenamiento total de la organización no quede negativo"""
        extra_storage_gb = self.cleaned_data.get('extra_storage_gb', 0)
        
        # Si es una nueva organización, no hay restricciones
        if not self.instance.pk:
            return extra_storage_gb
        
        # Obtener el límite del plan base
        current_org = Organization.objects.get(pk=self.instance.pk)
        plan_limit = 0
        if hasattr(current_org, 'subscription') and current_org.subscription:
            plan_limit = current_org.subscription.plan.max_storage_gb
        else:
            plan_limit = 75  # Fallback
        
        # Calcular el nuevo límite total
        new_total_limit = plan_limit + extra_storage_gb
        
        # Validar que el límite total no sea negativo
        if new_total_limit < 0:
            raise ValidationError(
                f"El almacenamiento total no puede ser negativo. "
                f"Plan base: {plan_limit} GB + Extra: {extra_storage_gb} GB = {new_total_limit} GB."
            )
        
        return extra_storage_gb

@admin.register(Organization)
class OrganizationAdmin(ImportExportModelAdmin):
    resource_class = OrganizationResource
    form = OrganizationAdminForm
    list_display = ['name', 'is_active', 'user_count', 'get_storage_info', 'get_subscription_status', 'get_subscription_link', 'created_at']
    list_filter = ['is_active', 'created_at', 'subscription__plan__display_name', 'subscription__subscription_status']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'user_count', 'get_subscription_status', 'get_subscription_link']
    
    actions = ['activate_organizations', 'deactivate_organizations', 'reduce_extra_storage', 'add_extra_storage']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Almacenamiento', {
            'fields': ('extra_storage_gb',),
            'description': '💾 <strong>GB Extras:</strong> Puedes aumentar o disminuir libremente según el pago del cliente. El sistema validará que el almacenamiento total (plan + extras) no quede negativo.',
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
    
    def get_storage_info(self, obj):
        """Muestra información del almacenamiento de la organización."""
        try:
            from apps.orgs.storage_service import StorageService
            storage_data = StorageService.get_storage_summary(obj)
            
            # Plan base + extras
            plan_limit = 0
            if hasattr(obj, 'subscription') and obj.subscription:
                plan_limit = obj.subscription.plan.max_storage_gb
            else:
                plan_limit = 75  # Fallback
            
            total_limit = plan_limit + obj.extra_storage_gb
            
            # Color basado en el porcentaje de uso
            if storage_data['percentage'] >= 90:
                color = '#E74C3C'  # Rojo
            elif storage_data['percentage'] >= 75:
                color = '#F39C12'  # Naranja
            else:
                color = '#27AE60'  # Verde
            
            storage_text = f"{round(storage_data['used_gb'], 2)} GB / {total_limit} GB"
            if obj.extra_storage_gb > 0:
                storage_text += f" (+{obj.extra_storage_gb} GB extra)"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span><br>'
                '<small style="color: #555;">{}% usado</small>',
                color,
                storage_text,
                round(storage_data['percentage'])
            )
        except Exception as e:
            return format_html('<span style="color: #C0392B;">Error al calcular</span>')
    get_storage_info.short_description = 'Almacenamiento'
    
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
    
    def reduce_extra_storage(self, request, queryset):
        """Reducir almacenamiento extra de organizaciones seleccionadas"""
        from apps.orgs.storage_service import StorageService
        
        reduced_count = 0
        blocked_count = 0
        
        for org in queryset:
            try:
                # Obtener uso actual
                storage_data = StorageService.calculate_storage_usage(org)
                used_gb = storage_data['total_gb']
                
                # Calcular límite del plan base
                plan_limit = 0
                if hasattr(org, 'subscription') and org.subscription:
                    plan_limit = org.subscription.plan.max_storage_gb
                else:
                    plan_limit = 75
                
                # Verificar si se puede reducir completamente el extra storage
                if used_gb <= plan_limit:
                    # Puede reducir todo el extra storage
                    org.extra_storage_gb = 0
                    org.save()
                    reduced_count += 1
                else:
                    # Calcular el mínimo extra storage necesario
                    needed_extra = max(0, used_gb - plan_limit)
                    minimum_extra = int(needed_extra) + 1  # Redondear hacia arriba y dejar 1 GB de margen
                    
                    if minimum_extra < org.extra_storage_gb:
                        org.extra_storage_gb = minimum_extra
                        org.save()
                        reduced_count += 1
                    else:
                        blocked_count += 1
                        
            except Exception as e:
                blocked_count += 1
        
        if reduced_count > 0:
            self.message_user(
                request, 
                f"✅ Se redujo el almacenamiento extra de {reduced_count} organizaciones.",
                messages.SUCCESS
            )
        
        if blocked_count > 0:
            self.message_user(
                request,
                f"⚠️ No se pudo reducir el almacenamiento de {blocked_count} organizaciones por exceder el uso actual.",
                messages.WARNING
            )
    
    reduce_extra_storage.short_description = "📉 Reducir almacenamiento extra seguro"
    
    def add_extra_storage(self, request, queryset):
        """Agregar 10 GB de almacenamiento extra a organizaciones seleccionadas"""
        updated = 0
        
        for org in queryset:
            org.extra_storage_gb += 10
            org.save()
            updated += 1
        
        self.message_user(
            request,
            f"📈 Se agregaron 10 GB extra a {updated} organizaciones.",
            messages.SUCCESS
        )
    
    add_extra_storage.short_description = "📈 Agregar 10 GB extra"

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
