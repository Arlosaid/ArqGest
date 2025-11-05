# apps/plans/admin.py
from django import forms
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils import timezone
from datetime import timedelta
from .models import Plan, Subscription, UpgradeRequest, Payment, RenewalRequest
from import_export import resources
from import_export.admin import ImportExportModelAdmin
import logging

logger = logging.getLogger(__name__)

# --- Recursos para Import/Export ---

class PlanResource(resources.ModelResource):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'display_name', 'price', 'max_users', 'trial_days', 'billing_cycle_days', 'is_active')
        export_order = fields

class SubscriptionResource(resources.ModelResource):
    class Meta:
        model = Subscription
        fields = ('id', 'organization__name', 'plan__name', 'start_date', 'end_date', 'subscription_status')
        export_order = fields

# --- Formularios para Acciones ---

# Formulario simplificado removido para evitar conflictos

class ExtendSubscriptionForm(forms.Form):
    days = forms.IntegerField(
        label="Días a extender",
        required=True,
        min_value=1,
        help_text="Número de días para extender la suscripción."
    )
    reason = forms.CharField(
        label="Razón de la extensión",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Opcional: explique por qué se realiza esta extensión."
    )

class ChangePlanForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        label="Nuevo Plan",
        required=True
    )

# --- ModelAdmin ---

@admin.register(Plan)
class PlanAdmin(ImportExportModelAdmin):
    resource_class = PlanResource
    list_display = ('display_name', 'name', 'price', 'max_users', 'trial_days', 'billing_cycle_days', 'grace_period_days', 'is_active')
    list_filter = ('is_active', 'name')
    search_fields = ('name', 'display_name')
    ordering = ('price',)
    fieldsets = (
        ('Información Principal', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Configuración del Plan', {
            'fields': ('price', 'max_users', 'trial_days', 'billing_cycle_days', 'grace_period_days')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_method', 'amount', 'status', 'created_at', 'description', 'days_added', 'old_end_date', 'new_end_date')
    can_delete = False
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Subscription)
class SubscriptionAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionResource
    list_display = ('organization', 'get_founder_indicator', 'plan', 'subscription_status', 'end_date_formatted', 'days_remaining_display', 'is_active')
    list_filter = ('subscription_status', 'plan__name', 'organization__is_founder_member')
    search_fields = ('organization__name', 'plan__display_name')
    list_select_related = ('organization', 'plan')
    
    readonly_fields = ('start_date', 'grace_end_date', 'created_at', 'updated_at', 'days_remaining_display')
    
    inlines = [PaymentInline]
    actions = ['process_selected_payments', 'extend_subscription_action', 'change_plan_action']
    
    def get_form(self, request, obj=None, **kwargs):
        """Personalizar el formulario para establecer valores por defecto"""
        form = super().get_form(request, obj, **kwargs)
        
        # Si es una nueva suscripción, establecer default de 30 días
        if obj is None:
            now = timezone.localtime(timezone.now())
            default_end_date = now + timedelta(days=30)
            form.base_fields['end_date'].initial = default_end_date
            form.base_fields['end_date'].help_text = (
                "Fecha y hora de vencimiento de la suscripción. "
                f"Se ha establecido por defecto a 30 días desde ahora ({default_end_date.strftime('%d/%m/%Y %H:%M')} México)."
            )
        
        return form

    def get_fieldsets(self, request, obj=None):
        # Configuración diferente para crear vs editar
        if obj:  # Editando suscripción existente
            return (
                ("Información General", {
                    'fields': ('organization', 'plan', 'subscription_status')
                }),
                ("Fechas Clave", {
                    'fields': ('start_date', 'end_date', 'grace_end_date', 'days_remaining_display'),
                    'description': 'Todas las fechas se muestran en zona horaria de México (UTC-6)'
                }),
                ("Timestamps", {
                    'fields': ('created_at', 'updated_at')
                }),
            )
        else:  # Creando nueva suscripción
            return (
                ("Información General", {
                    'fields': ('organization', 'plan')
                }),
                ("Configuración de Fechas", {
                    'fields': ('end_date',),
                    'description': 'La fecha de vencimiento se establece por defecto a 30 días desde ahora en zona horaria de México (UTC-6)'
                }),
            )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('organization', 'subscription_status', 'start_date', 'grace_end_date', 'created_at', 'updated_at', 'days_remaining_display')
        return self.readonly_fields
    
    def add_view(self, request, form_url='', extra_context=None):
        organization_id = request.GET.get('organization')
        if organization_id:
            request.GET = request.GET.copy()
            request.GET['organization'] = organization_id
        return super().add_view(request, form_url, extra_context)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_status()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('plan', 'organization')

    @admin.display(description="Fundador", ordering='organization__is_founder_member')
    def get_founder_indicator(self, obj):
        if obj.organization.is_founder_member:
            return format_html('<span style="color: #F39C12; font-weight: bold;">FUNDADOR $249</span>')
        return '-'

    @admin.display(description="Estado", ordering='subscription_status')
    def is_active(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">● Activa</span>')
        elif obj.is_in_grace_period:
            return format_html('<span style="color: orange;">● En Gracia</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">● Expirada</span>')
        return "Desconocido"

    @admin.display(description="Fecha de Vencimiento", ordering='end_date')
    def end_date_formatted(self, obj):
        if obj.end_date:
            # Convertir a zona horaria local para mostrar
            local_time = timezone.localtime(obj.end_date)
            return f"{local_time.strftime('%d de %b de %Y, %H:%M')} (México)"
        return "N/A"

    @admin.display(description="Días Restantes")
    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if obj.is_expired:
            return format_html('<span style="color: red;">Expirado</span>')
        if obj.is_in_grace_period:
            return format_html(f'<span style="color: orange;">{days} día(s) de gracia</span>')
        return f"{days} día(s)"

    @admin.action(description="Procesar pago recibido y extender suscripción")
    def process_selected_payments(self, request, queryset):
        processed_count = 0
        for subscription in queryset:
            try:
                payment_result = subscription.process_payment(
                    amount=subscription.plan.price,
                    processed_by=f"{request.user.email} (ID: {request.user.pk})"
                )
                if payment_result.get('success'):
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error procesando pago para {subscription}: {e}")
                self.message_user(request, f"Error al procesar el pago para {subscription.organization.name}.", messages.ERROR)
        
        if processed_count > 0:
            self.message_user(request, f"{processed_count} suscripciones han sido extendidas exitosamente.", messages.SUCCESS)

    @admin.action(description="Extender suscripción manualmente")
    def extend_subscription_action(self, request, queryset):
        if 'apply' in request.POST:
            form = ExtendSubscriptionForm(request.POST)
            if form.is_valid():
                days = form.cleaned_data['days']
                reason = form.cleaned_data['reason']
                extended_count = 0
                for subscription in queryset:
                    try:
                        subscription.extend_subscription(
                            days=days,
                            processed_by=f"{request.user.email} (ID: {request.user.pk})",
                            reason=reason
                        )
                        extended_count += 1
                    except Exception as e:
                        logger.error(f"Error extendiendo suscripción para {subscription.organization.name}: {e}")
                        self.message_user(request, f"Error al extender la suscripción de {subscription.organization.name}.", messages.ERROR)
                
                if extended_count > 0:
                    self.message_user(request, f"{extended_count} suscripciones han sido extendidas por {days} días.", messages.SUCCESS)
                return
        else:
            form = ExtendSubscriptionForm()

        return render(request, 'admin/extend_subscription_intermediate.html', context={
            'subscriptions': queryset,
            'form': form
        })
        
    @admin.action(description="Cambiar plan manualmente")
    def change_plan_action(self, request, queryset):
        if 'apply' in request.POST:
            form = ChangePlanForm(request.POST)
            if form.is_valid():
                new_plan = form.cleaned_data['plan']
                changed_count = 0
                for subscription in queryset:
                    if subscription.plan == new_plan:
                        self.message_user(request, f"La suscripción de {subscription.organization.name} ya tiene el plan {new_plan.display_name}.", messages.WARNING)
                        continue
                    try:
                        subscription.switch_plan(
                            new_plan=new_plan,
                            processed_by=f"{request.user.email} (ID: {request.user.pk})"
                        )
                        changed_count += 1
                    except Exception as e:
                        logger.error(f"Error cambiando el plan para {subscription.organization.name}: {e}")
                        self.message_user(request, f"Error al cambiar el plan de {subscription.organization.name}.", messages.ERROR)
                
                if changed_count > 0:
                    self.message_user(request, f"Se cambió el plan a {new_plan.display_name} para {changed_count} suscripciones.", messages.SUCCESS)
                return
        else:
            form = ChangePlanForm()

        return render(request, 'admin/change_plan_intermediate.html', context={
            'subscriptions': queryset,
            'form': form
        })

@admin.register(UpgradeRequest)
class UpgradeRequestAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'current_plan', 'requested_plan', 
        'amount', 'status_display', 'created_at', 'approved_by', 'actions_column'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['organization__name']
    readonly_fields = [
        'organization', 'current_plan', 'requested_plan', 'amount', 'status',
        'created_at', 'updated_at', 'approved_by'
    ]
    ordering = ['-created_at']
    actions = ['approve_selected_requests', 'reject_selected_requests']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'current_plan', 'requested_plan'
        )

    def status_display(self, obj):
        status_map = {
            'pending': ('orange', 'Pendiente'),
            'approved': ('green', 'Aprobado'),
            'rejected': ('red', 'Rechazado'),
        }
        color, text = status_map.get(obj.status, ('black', obj.get_status_display()))
        return format_html('<b style="color: {};">{}</b>', color, text)
    status_display.short_description = 'Estado'
    
    def approve_selected_requests(self, request, queryset):
        approved_count = 0
        for req in queryset.filter(status='pending'):
            result = req.approve(request.user)
            if result['success']:
                approved_count += 1
            self.message_user(request, f'{approved_count} solicitudes de upgrade aprobadas.', messages.SUCCESS)
    approve_selected_requests.short_description = "Aprobar solicitudes seleccionadas"

    def reject_selected_requests(self, request, queryset):
        rejected_count = 0
        for req in queryset.filter(status='pending'):
            result = req.reject(request.user)
            if result['success']:
                rejected_count += 1
        if rejected_count:
            self.message_user(request, f'{rejected_count} solicitudes de upgrade rechazadas.', messages.SUCCESS)
        else:
            self.message_user(request, 'No había solicitudes pendientes para rechazar.', messages.WARNING)
    reject_selected_requests.short_description = "Rechazar solicitudes seleccionadas"

    # --- Botones por fila en la lista ---
    @admin.display(description='Acciones')
    def actions_column(self, obj):
        if obj.status != 'pending':
            return format_html('<span style="color: #888;">—</span>')
        approve_url = reverse('admin:plans_upgraderequest_approve', args=[obj.pk])
        reject_url = reverse('admin:plans_upgraderequest_reject', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="margin-right:6px;">Aprobar</a>'
            '<a class="button" href="{}" style="background:#cc0000;border-color:#cc0000;">Rechazar</a>',
            approve_url,
            reject_url
        )

    # --- URLs personalizadas para acciones rápidas ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/approve/', self.admin_site.admin_view(self.approve_view), name='plans_upgraderequest_approve'),
            path('<int:pk>/reject/', self.admin_site.admin_view(self.reject_view), name='plans_upgraderequest_reject'),
        ]
        return custom_urls + urls

    def approve_view(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            self.message_user(request, 'Solicitud no encontrada.', messages.ERROR)
            return redirect('..')
        if obj.status != 'pending':
            self.message_user(request, 'La solicitud no está pendiente.', messages.WARNING)
            return redirect('..')
        result = obj.approve(request.user)
        if result.get('success'):
            self.message_user(request, 'Solicitud aprobada y suscripción actualizada.', messages.SUCCESS)
        else:
            self.message_user(request, f"No se pudo aprobar la solicitud: {result.get('error')}", messages.ERROR)
        return redirect('..')

    def reject_view(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            self.message_user(request, 'Solicitud no encontrada.', messages.ERROR)
            return redirect('..')
        if obj.status != 'pending':
            self.message_user(request, 'La solicitud no está pendiente.', messages.WARNING)
            return redirect('..')
        result = obj.reject(request.user)
        if result.get('success'):
            self.message_user(request, 'Solicitud rechazada.', messages.SUCCESS)
        else:
            self.message_user(request, f"No se pudo rechazar la solicitud: {result.get('error')}", messages.ERROR)
        return redirect('..')

    def save_model(self, request, obj, form, change):
        """
        Evita que un cambio manual del campo 'status' salte la lógica de negocio.
        Si alguien intenta marcar como 'approved' desde el formulario, ejecutamos approve().
        """
        if change and obj.pk:
            try:
                original = UpgradeRequest.objects.get(pk=obj.pk)
            except UpgradeRequest.DoesNotExist:
                original = None

            # Si el original estaba pendiente y en el form viene aprobado, usar approve()
            new_status = form.cleaned_data.get('status') if form is not None else None
            if original and original.status == 'pending' and new_status == 'approved':
                result = original.approve(request.user)
                if result.get('success'):
                    self.message_user(request, 'Solicitud aprobada y suscripción actualizada.', messages.SUCCESS)
                else:
                    self.message_user(request, f"No se pudo aprobar la solicitud: {result.get('error')}", messages.ERROR)
                return  # No llamar a super() para evitar doble guardado

            # Si el original estaba pendiente y en el form viene rechazado, usar reject()
            if original and original.status == 'pending' and new_status == 'rejected':
                result = original.reject(request.user)
                if result.get('success'):
                    self.message_user(request, 'Solicitud rechazada.', messages.SUCCESS)
                else:
                    self.message_user(request, f"No se pudo rechazar la solicitud: {result.get('error')}", messages.ERROR)
                return

        # Por defecto, comportamiento estándar
        return super().save_model(request, obj, form, change)

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    # No se define resource_class para que sea de solo lectura
    list_display = [
        'subscription', 'amount', 'payment_method', 'payment_type', 'status', 
        'processed_by', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'payment_type', 'created_at']
    search_fields = ['subscription__organization__name', 'processed_by']
    readonly_fields = [
        'subscription', 'amount', 'payment_method', 'payment_type', 'status',
        'processed_by', 'description', 'days_added', 'old_end_date',
        'new_end_date', 'created_at'
    ]
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
        
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription__organization')

@admin.register(RenewalRequest)
class RenewalRequestAdmin(ImportExportModelAdmin):
    list_display = [
        'organization', 'subscription', 'renewal_amount', 'renewal_days', 
        'status', 'created_at', 'processed_at', 'approved_by'
    ]
    list_filter = ['status', 'created_at', 'processed_at']
    search_fields = ['organization__name', 'subscription__plan__display_name', 'reason']
    readonly_fields = [
        'organization', 'subscription', 'renewal_amount', 'renewal_days', 
        'created_at', 'updated_at', 'processed_at', 'approved_by'
    ]
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('organization', 'subscription', 'status')
        }),
        ('Detalles de Renovación', {
            'fields': ('renewal_amount', 'renewal_days')
        }),
        ('Motivo', {
            'fields': ('reason',),
            'classes': ('collapse',)
        }),
        ('Procesamiento', {
            'fields': ('approved_by', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
    actions = ['approve_selected_renewals', 'reject_selected_renewals']

    def save_model(self, request, obj, form, change):
        """
        Evita que un cambio manual del campo 'status' salte la lógica de negocio.
        Si alguien marca como 'approved' o 'rejected' desde el formulario, ejecutamos approve()/reject().
        """
        if change and obj.pk:
            try:
                original = RenewalRequest.objects.get(pk=obj.pk)
            except RenewalRequest.DoesNotExist:
                original = None

            new_status = form.cleaned_data.get('status') if form is not None else None

            # Si el original estaba pendiente y en el form viene aprobado, usar approve()
            if original and original.status == 'pending' and new_status == 'approved':
                result = original.approve(request.user)
                if result.get('success'):
                    self.message_user(request, 'Renovación aprobada y suscripción extendida.', messages.SUCCESS)
                else:
                    self.message_user(request, f"No se pudo aprobar la renovación: {result.get('error')}", messages.ERROR)
                return  # No llamar a super() para evitar doble guardado

            # Si el original estaba pendiente y en el form viene rechazado, usar reject()
            if original and original.status == 'pending' and new_status == 'rejected':
                result = original.reject(request.user, "Rechazado desde admin")
                if result.get('success'):
                    self.message_user(request, 'Renovación rechazada.', messages.SUCCESS)
                else:
                    self.message_user(request, f"No se pudo rechazar la renovación: {result.get('error')}", messages.ERROR)
                return

        # Por defecto, comportamiento estándar
        return super().save_model(request, obj, form, change)

    @admin.action(description="Aprobar solicitudes seleccionadas")
    def approve_selected_renewals(self, request, queryset):
        approved_count = 0
        for renewal_request in queryset.filter(status='pending'):
            try:
                result = renewal_request.approve(request.user)
                if result.get('success'):
                    approved_count += 1
                else:
                    self.message_user(
                        request, 
                        f"Error aprobando renovación para {renewal_request.organization.name}: {result.get('error')}", 
                        messages.ERROR
                    )
            except Exception as e:
                logger.error(f"Error aprobando renovación {renewal_request.id}: {e}", exc_info=True)
                self.message_user(
                    request, 
                    f"Error aprobando renovación para {renewal_request.organization.name}", 
                    messages.ERROR
                )
        
        if approved_count > 0:
            self.message_user(
                request, 
                f"{approved_count} solicitud{'es' if approved_count != 1 else ''} de renovación aprobada{'s' if approved_count != 1 else ''} exitosamente.", 
                messages.SUCCESS
            )

    @admin.action(description="Rechazar solicitudes seleccionadas")
    def reject_selected_renewals(self, request, queryset):
        rejected_count = 0
        for renewal_request in queryset.filter(status='pending'):
            try:
                result = renewal_request.reject(request.user, "Rechazado desde admin")
                if result.get('success'):
                    rejected_count += 1
                else:
                    self.message_user(
                        request, 
                        f"Error rechazando renovación para {renewal_request.organization.name}: {result.get('error')}", 
                        messages.ERROR
                    )
            except Exception as e:
                logger.error(f"Error rechazando renovación {renewal_request.id}: {e}", exc_info=True)
                self.message_user(
                    request, 
                    f"Error rechazando renovación para {renewal_request.organization.name}", 
                    messages.ERROR
                )
        
        if rejected_count > 0:
            self.message_user(
                request, 
                f"{rejected_count} solicitud{'es' if rejected_count != 1 else ''} de renovación rechazada{'s' if rejected_count != 1 else ''}.", 
                messages.SUCCESS
            )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'subscription__plan'
        )

admin.site.site_header = "ARC Manager - Administración"
admin.site.site_title = "ARC Manager Admin"
admin.site.index_title = "Panel de Administración"
