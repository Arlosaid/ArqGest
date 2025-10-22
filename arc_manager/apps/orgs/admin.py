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
    """Resource para exportar organizaciones con manejo seguro de subscriptions."""
    
    def dehydrate_subscription__plan__name(self, organization):
        """Manejar organizaciones sin subscription."""
        try:
            if hasattr(organization, 'subscription') and organization.subscription:
                return organization.subscription.plan.name
            return 'Sin suscripción'
        except Exception:
            return 'Sin suscripción'
    
    def dehydrate_subscription__end_date(self, organization):
        """Manejar organizaciones sin subscription."""
        try:
            if hasattr(organization, 'subscription') and organization.subscription:
                return organization.subscription.end_date
            return None
        except Exception:
            return None
    
    class Meta:
        model = Organization
        fields = ('id', 'name', 'is_active', 'created_at')
        export_order = fields

class ClientResource(resources.ModelResource):
    """Resource para exportar clientes con manejo seguro de organizaciones."""
    
    def dehydrate_organization__name(self, client):
        """Manejar clientes sin organización (no debería pasar con CASCADE, pero por seguridad)."""
        try:
            if client.organization:
                return client.organization.name
            return 'Sin organización'
        except Exception:
            return 'Sin organización'
    
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
        try:
            current_org = Organization.objects.get(pk=self.instance.pk)
            plan_limit = 0
            if hasattr(current_org, 'subscription') and current_org.subscription:
                plan_limit = current_org.subscription.plan.max_storage_gb
            else:
                plan_limit = 75  # Fallback
        except Organization.DoesNotExist:
            # Si la organización no existe, usar fallback
            plan_limit = 75
        
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
    list_display = ['name', 'get_active_status', 'get_founder_badge', 'user_count', 'get_storage_info', 'get_subscription_status', 'get_subscription_link', 'created_at']
    list_filter = ['is_active', 'is_founder_member', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'user_count', 'get_subscription_status', 'get_subscription_link', 'get_users_display']
    
    actions = ['activate_organizations', 'deactivate_organizations', 'mark_as_founder', 'unmark_as_founder', 'reduce_extra_storage', 'add_extra_storage']
    
    def delete_model(self, request, obj):
        """
        Al eliminar una organización, se eliminan automáticamente todos sus usuarios,
        proyectos, archivos y clientes debido a CASCADE.
        """
        user_count = obj.users.count()
        org_name = obj.name
        
        super().delete_model(request, obj)
        
        if user_count > 0:
            self.message_user(
                request,
                f"Organización '{org_name}' eliminada junto con {user_count} usuario(s) y todos sus datos asociados.",
                messages.WARNING
            )
    
    def delete_queryset(self, request, queryset):
        """
        Al eliminar organizaciones, se eliminan automáticamente todos sus usuarios,
        proyectos, archivos y clientes debido a CASCADE.
        """
        total_users = sum(org.users.count() for org in queryset)
        deleted_count = queryset.count()
        
        super().delete_queryset(request, queryset)
        
        if total_users > 0:
            self.message_user(
                request,
                f"Se eliminaron {deleted_count} organización(es) junto con {total_users} usuario(s) y todos sus datos asociados.",
                messages.WARNING
            )
        else:
            self.message_user(
                request,
                f"Se eliminaron {deleted_count} organización(es) correctamente.",
                messages.SUCCESS
            )
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Almacenamiento', {
            'fields': ('extra_storage_gb',),
            'description': '💾 <strong>GB Extras:</strong> Puedes aumentar o disminuir libremente según el pago del cliente. El sistema validará que el almacenamiento total (plan + extras) no quede negativo.',
        }),
        ('Membresía Fundadora', {
            'fields': ('is_founder_member',),
            'description': '🌟 <strong>Miembros Fundadores:</strong> Precio especial de $249/mes en lugar de $299/mes. El descuento se aplicará automáticamente.',
            'classes': ('collapse',)
        }),
        ('Suscripción', {
            'fields': ('get_subscription_status', 'get_subscription_link'),
            'description': '📝 Para gestionar planes y suscripciones, usa el módulo "Suscripciones" del admin.',
            'classes': ('collapse',)
        }),
        ('Usuarios de la Organización', {
            'fields': ('get_users_display',),
            'description': '👥 <strong>Usuarios:</strong> Lista de todos los usuarios con sus roles y emails. Los administradores aparecen destacados.',
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
        # Prefetch de subscription de forma segura - solo si existe
        try:
            # Verificar que la relación subscription existe antes de hacer prefetch
            from apps.plans.models import Subscription
            if hasattr(Organization, 'subscription'):
                queryset = queryset.prefetch_related('subscription__plan')
        except Exception as e:
            # Si hay problemas con el prefetch, usar solo el queryset base
            print(f"Warning: No se pudo hacer prefetch de subscription: {e}")
            pass
        queryset = queryset.annotate(user_count_admin=models.Count('users'))
        return queryset

    def get_active_status(self, obj):
        """Muestra el estado de la organización con colores."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">✓ ACTIVA</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">✕ INACTIVA</span>'
        )
    get_active_status.short_description = 'Estado'
    get_active_status.admin_order_field = 'is_active'
    
    def get_founder_badge(self, obj):
        """Muestra una insignia si es miembro fundador."""
        if obj.is_founder_member:
            return format_html(
                '<span style="background-color: #F39C12; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">⭐ FUNDADOR $249</span>'
            )
        return '-'
    get_founder_badge.short_description = 'Membresía'
    get_founder_badge.admin_order_field = 'is_founder_member'

    def user_count(self, obj):
        """Muestra el total de usuarios desde la anotación o contando directamente."""
        try:
            # Si tiene la anotación (desde el queryset del admin)
            if hasattr(obj, 'user_count_admin'):
                return f"{obj.user_count_admin} usuarios"
            else:
                # Contar directamente si no hay anotación
                count = obj.users.count()
                return f"{count} usuarios"
        except Exception:
            # Fallback en caso de error
            return "0 usuarios"
    user_count.short_description = 'Usuarios'
    user_count.admin_order_field = 'user_count_admin' # Permite ordenar por esta columna

    def get_subscription_status(self, obj):
        """Muestra el estado de la suscripción de forma simple y visual."""
        try:
            # Verificar si la organización tiene suscripción de forma segura
            if hasattr(obj, 'subscription'):
                subscription = getattr(obj, 'subscription', None)
                if subscription:
                    plan = getattr(subscription, 'plan', None)
                    if plan:
                        status_text = getattr(subscription, 'get_subscription_status_display', lambda: 'Sin estado')()
                        
                        color = 'black'
                        if getattr(subscription, 'is_active', False):
                            color = 'green'
                            if hasattr(subscription, 'subscription_status') and 'trial' in str(subscription.subscription_status):
                                color = '#E67E22'
                        elif getattr(subscription, 'is_in_grace_period', False):
                            color = '#F39C12'
                        elif getattr(subscription, 'is_expired', False):
                            color = '#E74C3C'

                        plan_name = getattr(plan, 'display_name', getattr(plan, 'name', 'Plan desconocido'))
                        days_remaining = getattr(subscription, 'days_remaining', 0)

                        return format_html(
                            '<span style="color: {}; font-weight: bold;">{}</span><br>'
                            '<small style="color: #555;">{} - {} días restantes</small>',
                            color,
                            status_text,
                            plan_name,
                            days_remaining
                        )
        except Exception as e:
            # Log del error para debugging
            print(f"Error en get_subscription_status para org {obj.id}: {e}")
            pass
        return format_html('<span style="color: #C0392B; font-weight: bold;">Sin suscripción</span>')
    get_subscription_status.short_description = 'Estado de Suscripción'
    
    def get_subscription_link(self, obj):
        """Proporciona un enlace para gestionar la suscripción."""
        try:
            if hasattr(obj, 'subscription'):
                subscription = getattr(obj, 'subscription', None)
                if subscription and hasattr(subscription, 'pk'):
                    subscription_url = reverse('admin:plans_subscription_change', args=[subscription.pk])
                    return format_html('<a href="{}" class="button">📝 Gestionar suscripción</a>', subscription_url)
        except Exception as e:
            print(f"Error en get_subscription_link para org {obj.id}: {e}")
            pass
        try:
            add_subscription_url = reverse('admin:plans_subscription_add') + f'?organization={obj.pk}'
            return format_html('<a href="{}" class="button">➕ Crear suscripción</a>', add_subscription_url)
        except Exception as e:
            print(f"Error creando enlace de suscripción para org {obj.id}: {e}")
            return format_html('<span style="color: #C0392B;">Error en enlace</span>')
    get_subscription_link.short_description = 'Gestión'
    
    def get_storage_info(self, obj):
        """Muestra información del almacenamiento de la organización."""
        try:
            from apps.orgs.storage_service import StorageService
            storage_data = StorageService.get_storage_summary(obj)
            
            # Plan base + extras - verificar de forma segura
            plan_limit = 0
            if hasattr(obj, 'subscription'):
                subscription = getattr(obj, 'subscription', None)
                if subscription:
                    plan = getattr(subscription, 'plan', None)
                    if plan:
                        plan_limit = getattr(plan, 'max_storage_gb', 75)
            else:
                plan_limit = 75  # Fallback
            
            total_limit = plan_limit + getattr(obj, 'extra_storage_gb', 0)
            
            # Color basado en el porcentaje de uso
            percentage = storage_data.get('percentage', 0)
            if percentage >= 90:
                color = '#E74C3C'  # Rojo
            elif percentage >= 75:
                color = '#F39C12'  # Naranja
            else:
                color = '#27AE60'  # Verde
            
            used_gb = storage_data.get('used_gb', 0)
            storage_text = f"{round(used_gb, 2)} GB / {total_limit} GB"
            extra_storage = getattr(obj, 'extra_storage_gb', 0)
            if extra_storage > 0:
                storage_text += f" (+{extra_storage} GB extra)"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span><br>'
                '<small style="color: #555;">{}% usado</small>',
                color,
                storage_text,
                round(percentage)
            )
        except Exception as e:
            print(f"Error en get_storage_info para org {obj.id}: {e}")
            return format_html('<span style="color: #C0392B;">Error al calcular</span>')
    get_storage_info.short_description = 'Almacenamiento'
    
    def activate_organizations(self, request, queryset):
        """Activar organizaciones seleccionadas"""
        total_users = sum(org.users.count() for org in queryset)
        updated = queryset.update(is_active=True)
        
        self.message_user(
            request, 
            f"✅ Se activaron {updated} organización(es). "
            f"Los {total_users} usuario(s) asociados ahora pueden acceder nuevamente.",
            messages.SUCCESS
        )
    activate_organizations.short_description = "✅ Activar organizaciones (restaurar acceso)"
    
    def deactivate_organizations(self, request, queryset):
        """Desactivar organizaciones seleccionadas"""
        total_users = sum(org.users.count() for org in queryset)
        updated = queryset.update(is_active=False)
        
        self.message_user(
            request,
            f"⚠️ Se desactivaron {updated} organización(es). "
            f"Los {total_users} usuario(s) asociados NO podrán acceder hasta que reactives la organización.",
            messages.WARNING
        )
    deactivate_organizations.short_description = "❌ Desactivar organizaciones (bloquear acceso)"
    
    def mark_as_founder(self, request, queryset):
        """Marcar organizaciones como miembros fundadores"""
        from django.utils import timezone
        from decimal import Decimal
        updated = 0
        # Descuento fijo: de $299 a $249 = 16.72% de descuento
        FOUNDER_DISCOUNT = Decimal('16.72')
        
        for org in queryset:
            if not org.is_founder_member:
                org.is_founder_member = True
                org.founder_joined_date = timezone.now()
                org.founder_discount_percentage = FOUNDER_DISCOUNT
                org.save()
                updated += 1
        self.message_user(request, f"⭐ Se marcaron {updated} organizaciones como miembros fundadores. Precio especial: $249/mes.", messages.SUCCESS)
    mark_as_founder.short_description = "⭐ Marcar como miembro fundador ($249/mes)"
    
    def unmark_as_founder(self, request, queryset):
        """Quitar el estatus de miembro fundador"""
        updated = queryset.filter(is_founder_member=True).update(is_founder_member=False)
        self.message_user(request, f"Se quitó el estatus de fundador a {updated} organizaciones.", messages.SUCCESS)
    unmark_as_founder.short_description = "Quitar estatus de fundador"
    
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
    
    def get_users_display(self, obj):
        """Muestra los usuarios de la organización con sus roles y emails"""
        from django.utils.html import format_html
        from django.urls import reverse
        
        try:
            users = obj.users.all().order_by('-is_org_admin', 'email')
            
            if not users.exists():
                return format_html('<span style="color: #7F8C8D;">Sin usuarios</span>')
            
            user_list = []
            for user in users:
                try:
                    # Determinar el rol
                    if user.is_superuser:
                        role_badge = '<span style="background: #E74C3C; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">SUPER</span>'
                    elif user.is_org_admin:
                        role_badge = '<span style="background: #F39C12; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">ADMIN</span>'
                    else:
                        role_badge = '<span style="background: #95A5A6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">USER</span>'
                    
                    # Estado del usuario
                    status_color = '#27AE60' if user.is_active else '#E74C3C'
                    status_text = 'Activo' if user.is_active else 'Inactivo'
                    
                    # Crear enlace al usuario
                    user_url = reverse('admin:accounts_user_change', args=[user.id])
                    
                    user_info = f'''
                        <div style="margin: 5px 0; padding: 8px; border: 1px solid #BDC3C7; border-radius: 4px; background: #F8F9FA;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                {role_badge}
                                <a href="{user_url}" style="color: #2C3E50; text-decoration: none; font-weight: 500;">{user.email}</a>
                                <span style="color: {status_color}; font-size: 11px;">{status_text}</span>
                            </div>
                            <div style="margin-top: 3px; color: #7F8C8D; font-size: 12px;">
                                {user.first_name} {user.last_name}
                            </div>
                        </div>
                    '''
                    user_list.append(user_info)
                except Exception as e:
                    # Si hay error con un usuario específico, continuar con los demás
                    user_list.append(f'<div style="color: #E74C3C;">Error con usuario: {e}</div>')
            
            return format_html(''.join(user_list))
        except Exception as e:
            return format_html('<span style="color: #E74C3C;">Error al cargar usuarios: {}</span>', str(e))
    
    get_users_display.short_description = 'Usuarios'
    get_users_display.allow_tags = True

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
