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
import logging
from core.structured_logging import log_error, log_info

logger = logging.getLogger('apps.orgs')

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
                plan_limit = 10  # Fallback
        except Organization.DoesNotExist:
            # Si la organización no existe, usar fallback
            plan_limit = 10
        
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
    
    def save_model(self, request, obj, form, change):
        """
        Hook de Django admin para guardar el modelo.
        Implementa logging estructurado para crear y actualizar organizaciones.
        """
        try:
            if change:
                # Es una actualización - capturar cambios
                changes = []
                
                # Campos a rastrear para el logging
                tracked_fields = {
                    'name': 'Nombre',
                    'is_active': 'Estado activo',
                    'is_founder_member': 'Miembro fundador',
                    'extra_storage_gb': 'Almacenamiento extra'
                }
                
                # Obtener la instancia original de la DB
                try:
                    original = Organization.objects.get(pk=obj.pk)
                    
                    for field_name, field_label in tracked_fields.items():
                        old_value = getattr(original, field_name)
                        new_value = getattr(obj, field_name)
                        
                        if old_value != new_value:
                            changes.append({
                                'field': field_name,
                                'field_label': field_label,
                                'old': old_value,
                                'new': new_value
                            })
                except Organization.DoesNotExist:
                    # Si no existe el original, tratarlo como creación
                    change = False
            
            # Guardar el objeto
            super().save_model(request, obj, form, change)
            
            # Logging estructurado
            if change and changes:
                # Detectar cambios críticos en is_active
                is_active_changed = any(c['field'] == 'is_active' for c in changes)
                
                if is_active_changed:
                    # Obtener el cambio específico de is_active
                    is_active_change = next(c for c in changes if c['field'] == 'is_active')
                    new_status = is_active_change['new']
                    old_status = is_active_change['old']
                    
                    # Contar usuarios afectados
                    user_count = obj.users.count()
                    
                    # Log WARNING para cambios de estado (crítico para seguridad)
                    logger.warning(
                        f"ORGANIZATION_STATUS_CHANGED | "
                        f"Organización '{obj.name}' (ID: {obj.id}) | "
                        f"Estado: {old_status} → {new_status} | "
                        f"Usuarios afectados: {user_count} | "
                        f"Admin: {request.user.email if request.user else 'Sistema'}",
                        extra={
                            'user_id': request.user.id if request.user else None,
                            'organization_id': obj.id,
                            'organization_name': obj.name,
                            'old_status': old_status,
                            'new_status': new_status,
                            'users_affected': user_count
                        }
                    )
                
                # ORGANIZATION_UPDATED (log general)
                log_info(
                    event='ORGANIZATION_UPDATED',
                    message=f"Organización '{obj.name}' actualizada con {len(changes)} cambio(s)",
                    logger_name='apps.orgs',
                    organization_id=obj.id,
                    organization_name=obj.name,
                    changes=changes,
                    updated_by=request.user.email if request.user else 'Sistema'
                )
                
                # Mensaje para el admin
                changes_text = ', '.join([f"{c['field_label']}" for c in changes])
                messages.success(
                    request,
                    f"Organización '{obj.name}' actualizada exitosamente. Cambios: {changes_text}"
                )
            else:
                # ORGANIZATION_CREATED
                log_info(
                    event='ORGANIZATION_CREATED',
                    message=f"Nueva organización creada: '{obj.name}'",
                    logger_name='apps.orgs',
                    organization_id=obj.id,
                    organization_name=obj.name,
                    is_active=obj.is_active,
                    is_founder=obj.is_founder_member,
                    extra_storage_gb=obj.extra_storage_gb,
                    created_by=request.user.email if request.user else 'Sistema'
                )
                
                messages.success(
                    request,
                    f"Organización '{obj.name}' creada exitosamente."
                )
                
        except Exception as e:
            # Log del error con detalles completos
            log_error(
                event='ORGANIZATION_SAVE_FAILED',
                error_code='ORG001',
                error_message=str(e),
                logger_name='apps.orgs',
                organization_name=getattr(obj, 'name', 'Desconocida'),
                action='update' if change else 'create',
                user_email=request.user.email if request.user else 'Sistema'
            )
            
            # Mensaje de error para el admin
            messages.error(
                request,
                f"Error al {'actualizar' if change else 'crear'} la organización: {str(e)}"
            )
            
            # Re-lanzar la excepción para que Django la maneje
            raise
    
    def delete_model(self, request, obj):
        """
        Al eliminar una organización:
        1. Se limpian TODOS los archivos de R2/S3 (carpeta organizations/{id}/)
        2. Se eliminan automáticamente usuarios, proyectos, archivos DB y clientes (CASCADE)
        """
        # Recolectar información antes de eliminar
        user_count = obj.users.count()
        org_name = obj.name
        org_id = obj.id
        
        try:
            # Contar archivos en DB (se eliminarán por CASCADE)
            from apps.files.models import ProjectFile
            files_count = ProjectFile.objects.filter(
                phase__project__organization=obj
            ).count()
        except Exception as e:
            files_count = 0
            log_error(
                event='ORGANIZATION_DELETE_COUNT_ERROR',
                error_code='ORG002',
                error_message=f"No se pudo contar archivos: {str(e)}",
                logger_name='apps.orgs',
                organization_id=org_id,
                organization_name=org_name
            )
        
        # 🔥 IMPORTANTE: Llamar a obj.delete() directamente para ejecutar el método personalizado
        # que limpia archivos de R2, NO usar super().delete_model() que usa queryset.delete()
        try:
            obj.delete()
            
            # Log único después de eliminar exitosamente (incluye toda la info relevante)
            log_info(
                event='ORGANIZATION_DELETED',
                message=f"Organización '{org_name}' eliminada exitosamente",
                logger_name='apps.orgs',
                organization_id=org_id,
                organization_name=org_name,
                files_deleted=files_count,
                users_deleted=user_count,
                deleted_by=request.user.email if request.user else 'Sistema'
            )
            
            # Mensaje de confirmación
            msg_parts = [f"Organización '{org_name}' eliminada"]
            
            if user_count > 0:
                msg_parts.append(f"{user_count} usuario(s)")
            
            if files_count > 0:
                msg_parts.append(f"{files_count} archivo(s) en DB")
                msg_parts.append("archivos eliminados de R2/S3")
            
            self.message_user(
                request,
                " junto con ".join(msg_parts) + ".",
                messages.WARNING
            )
            
            # Mensaje adicional sobre R2
            import os
            if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
                self.message_user(
                    request,
                    f"Los archivos de la carpeta 'organizations/{org_id}/' han sido eliminados de R2/S3.",
                    messages.INFO
                )
                
        except Exception as e:
            # Log del error
            log_error(
                event='ORGANIZATION_DELETE_FAILED',
                error_code='ORG003',
                error_message=str(e),
                logger_name='apps.orgs',
                organization_id=org_id,
                organization_name=org_name,
                deleted_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al eliminar la organización '{org_name}': {str(e)}"
            )
            
            raise
    
    def delete_queryset(self, request, queryset):
        """
        Al eliminar organizaciones en lote:
        1. Se limpian TODOS los archivos de R2/S3 de cada organización
        2. Se eliminan automáticamente usuarios, proyectos, archivos DB y clientes (CASCADE)
        """
        # Recolectar información antes de eliminar
        total_users = sum(org.users.count() for org in queryset)
        deleted_count = queryset.count()
        
        try:
            from apps.files.models import ProjectFile
            total_files = sum(
                ProjectFile.objects.filter(phase__project__organization=org).count()
                for org in queryset
            )
        except Exception as e:
            total_files = 0
            log_error(
                event='ORGANIZATION_BULK_DELETE_COUNT_ERROR',
                error_code='ORG004',
                error_message=f"No se pudo contar archivos: {str(e)}",
                logger_name='apps.orgs',
                organization_count=deleted_count
            )
        
        org_ids = list(queryset.values_list('id', flat=True))
        org_names = list(queryset.values_list('name', flat=True))
        
        # IMPORTANTE: Llamar a delete() de cada instancia para ejecutar limpieza de R2
        # NO usar super().delete_queryset() porque usa queryset.delete() que NO llama al método personalizado
        try:
            for org in queryset:
                org.delete()  # Esto SÍ ejecuta el método delete() con limpieza de R2
            
            # Log único después de eliminar exitosamente (incluye toda la info relevante)
            log_info(
                event='ORGANIZATION_BULK_DELETED',
                message=f"{deleted_count} organizaciones eliminadas exitosamente",
                logger_name='apps.orgs',
                organization_count=deleted_count,
                users_deleted=total_users,
                files_deleted=total_files,
                organization_ids=org_ids,
                organization_names=org_names,
                deleted_by=request.user.email if request.user else 'Sistema'
            )
            
            # Mensaje de confirmación
            msg_parts = [f"Se eliminaron {deleted_count} organización(es)"]
            
            if total_users > 0:
                msg_parts.append(f"{total_users} usuario(s)")
            
            if total_files > 0:
                msg_parts.append(f"{total_files} archivo(s) en DB y R2/S3")
            
            self.message_user(
                request,
                " junto con ".join(msg_parts) + ".",
                messages.WARNING
            )
            
            # Mensaje adicional sobre R2
            import os
            if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
                org_folders = ", ".join([f"organizations/{oid}/" for oid in org_ids[:3]])
                if deleted_count > 3:
                    org_folders += f" y {deleted_count - 3} más"
                
                self.message_user(
                    request,
                    f"Archivos eliminados de R2/S3: {org_folders}",
                    messages.INFO
                )
                
        except Exception as e:
            # Log del error
            log_error(
                event='ORGANIZATION_BULK_DELETE_FAILED',
                error_code='ORG005',
                error_message=str(e),
                logger_name='apps.orgs',
                organization_count=deleted_count,
                organization_ids=org_ids,
                deleted_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al eliminar organizaciones: {str(e)}"
            )
            
            raise
    
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
            'description': '<strong>Miembros Fundadores:</strong> Precio especial de $199/mes en lugar de $299/mes. El descuento se aplicará automáticamente.',
            'classes': ('collapse',)
        }),
        ('Suscripción', {
            'fields': ('get_subscription_status', 'get_subscription_link'),
            'description': 'Para gestionar planes y suscripciones, usa el módulo "Suscripciones" del admin.',
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
                '<span style="background-color: #F39C12; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">FUNDADOR $199</span>'
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
                    return format_html('<a href="{}" class="button" style="color: white;">Gestionar suscripción</a>', subscription_url)
        except Exception as e:
            logger.debug(f"Error en get_subscription_link para org {obj.id}: {e}")
            pass
        
        # Sin suscripción, mostrar botón para crear una
        create_subscription_url = reverse('admin:plans_subscription_add') + f'?organization={obj.id}'
        return format_html('<a href="{}" class="button" style="color: white; background-color: #417690;">Gestionar suscripción</a>', create_subscription_url)
    get_subscription_link.short_description = 'Gestión'
    
    def get_storage_info(self, obj):
        """Muestra información del almacenamiento de la organización."""
        try:
            from apps.orgs.storage_service import StorageService
            storage_data = StorageService.get_storage_summary(obj)
            
            # Usar el método del modelo que ya maneja el fallback correctamente
            total_limit = obj.get_total_storage_limit_gb()
            
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
        """
        Activar organizaciones seleccionadas con manejo robusto de errores.
        Si falla una organización, continúa con las demás y loguea el error.
        """
        total_users = 0
        org_ids = []
        org_names = []
        failed_orgs = []
        success_count = 0
        
        # Procesar cada organización individualmente para manejo de errores granular
        for org in queryset:
            try:
                # Contar usuarios antes de activar
                user_count = org.users.count()
                
                # Activar la organización
                org.is_active = True
                org.save()
                
                # Acumular estadísticas
                total_users += user_count
                org_ids.append(org.id)
                org_names.append(org.name)
                success_count += 1
                
            except Exception as e:
                # Log del error específico para esta organización
                log_error(
                    event='ORGANIZATION_ACTIVATE_ERROR',
                    error_code='ORG_ACTIVATE_001',
                    error_message=str(e),
                    logger_name='apps.orgs',
                    organization_id=org.id,
                    organization_name=org.name,
                    user_email=request.user.email if request.user else 'Sistema'
                )
                
                failed_orgs.append({
                    'id': org.id,
                    'name': org.name,
                    'error': str(e)
                })
        
        # Log de éxito (solo si hubo al menos una exitosa)
        if success_count > 0:
            logger.info(
                f"ORGANIZATIONS_ACTIVATED | "
                f"{success_count} organizaciones activadas | "
                f"Usuarios reactivados: {total_users} | "
                f"Orgs: {', '.join(org_names[:3])}" + (f" y {len(org_names)-3} más" if len(org_names) > 3 else "") + " | "
                f"Admin: {request.user.email if request.user else 'Sistema'}",
                extra={
                    'user_id': request.user.id if request.user else None,
                    'organization_ids': org_ids,
                    'organization_count': success_count,
                    'total_users_affected': total_users
                }
            )
        
        # Mensajes al admin
        if success_count > 0:
            self.message_user(
                request, 
                f"✅ Se activaron {success_count} organización(es). "
                f"Los {total_users} usuario(s) asociados ahora pueden acceder nuevamente.",
                messages.SUCCESS
            )
        
        if failed_orgs:
            # Log de resumen de errores
            logger.error(
                f"ORGANIZATIONS_ACTIVATE_FAILED | "
                f"{len(failed_orgs)} organizaciones fallaron | "
                f"Admin: {request.user.email if request.user else 'Sistema'}",
                extra={
                    'user_id': request.user.id if request.user else None,
                    'failed_count': len(failed_orgs),
                    'failed_organizations': failed_orgs
                }
            )
            
            # Mensaje de error al admin
            error_details = ', '.join([f"{f['name']}" for f in failed_orgs[:3]])
            if len(failed_orgs) > 3:
                error_details += f" y {len(failed_orgs)-3} más"
            
            self.message_user(
                request,
                f"❌ Error al activar {len(failed_orgs)} organización(es): {error_details}. "
                f"Revisa los logs para más detalles.",
                messages.ERROR
            )
    activate_organizations.short_description = "Activar organizaciones (restaurar acceso)"
    
    def deactivate_organizations(self, request, queryset):
        """
        Desactivar organizaciones seleccionadas con manejo robusto de errores.
        Si falla una organización, continúa con las demás y loguea el error.
        """
        total_users = 0
        org_ids = []
        org_names = []
        failed_orgs = []
        success_count = 0
        
        # Procesar cada organización individualmente para manejo de errores granular
        for org in queryset:
            try:
                # Contar usuarios antes de desactivar
                user_count = org.users.count()
                
                # Desactivar la organización
                org.is_active = False
                org.save()
                
                # Acumular estadísticas
                total_users += user_count
                org_ids.append(org.id)
                org_names.append(org.name)
                success_count += 1
                
            except Exception as e:
                # Log del error específico para esta organización
                log_error(
                    event='ORGANIZATION_DEACTIVATE_ERROR',
                    error_code='ORG_DEACTIVATE_001',
                    error_message=str(e),
                    logger_name='apps.orgs',
                    organization_id=org.id,
                    organization_name=org.name,
                    user_email=request.user.email if request.user else 'Sistema'
                )
                
                failed_orgs.append({
                    'id': org.id,
                    'name': org.name,
                    'error': str(e)
                })
        
        # Log de éxito (solo si hubo al menos una exitosa)
        if success_count > 0:
            logger.warning(
                f"ORGANIZATIONS_DEACTIVATED | "
                f"{success_count} organizaciones desactivadas | "
                f"Usuarios bloqueados: {total_users} | "
                f"Orgs: {', '.join(org_names[:3])}" + (f" y {len(org_names)-3} más" if len(org_names) > 3 else "") + " | "
                f"Admin: {request.user.email if request.user else 'Sistema'}",
                extra={
                    'user_id': request.user.id if request.user else None,
                    'organization_ids': org_ids,
                    'organization_count': success_count,
                    'total_users_affected': total_users
                }
            )
        
        # Mensajes al admin
        if success_count > 0:
            self.message_user(
                request,
                f"✅ Se desactivaron {success_count} organización(es). "
                f"Los {total_users} usuario(s) asociados NO podrán acceder hasta que reactives la organización.",
                messages.SUCCESS
            )
        
        if failed_orgs:
            # Log de resumen de errores
            logger.error(
                f"ORGANIZATIONS_DEACTIVATE_FAILED | "
                f"{len(failed_orgs)} organizaciones fallaron | "
                f"Admin: {request.user.email if request.user else 'Sistema'}",
                extra={
                    'user_id': request.user.id if request.user else None,
                    'failed_count': len(failed_orgs),
                    'failed_organizations': failed_orgs
                }
            )
            
            # Mensaje de error al admin
            error_details = ', '.join([f"{f['name']}" for f in failed_orgs[:3]])
            if len(failed_orgs) > 3:
                error_details += f" y {len(failed_orgs)-3} más"
            
            self.message_user(
                request,
                f"❌ Error al desactivar {len(failed_orgs)} organización(es): {error_details}. "
                f"Revisa los logs para más detalles.",
                messages.ERROR
            )
    deactivate_organizations.short_description = "Desactivar organizaciones (bloquear acceso)"
    
    def mark_as_founder(self, request, queryset):
        """Marcar organizaciones como miembros fundadores"""
        from django.utils import timezone
        from decimal import Decimal
        updated = 0
        # Descuento fijo: de $299 a $199 = 33.44% de descuento
        FOUNDER_DISCOUNT = Decimal('33.44')
        
        for org in queryset:
            if not org.is_founder_member:
                org.is_founder_member = True
                org.founder_joined_date = timezone.now()
                org.founder_discount_percentage = FOUNDER_DISCOUNT
                org.save()
                updated += 1
        self.message_user(request, f"Se marcaron {updated} organizaciones como miembros fundadores. Precio especial: $199/mes.", messages.SUCCESS)
    mark_as_founder.short_description = "Marcar como miembro fundador ($199/mes)"
    
    def unmark_as_founder(self, request, queryset):
        """Quitar el estatus de miembro fundador"""
        from decimal import Decimal
        updated = 0
        for org in queryset.filter(is_founder_member=True):
            org.is_founder_member = False
            org.founder_discount_percentage = Decimal('0')
            org.founder_joined_date = None
            org.save()
            updated += 1
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
                    plan_limit = 10
                
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
                f"Se redujo el almacenamiento extra de {reduced_count} organizaciones.",
                messages.SUCCESS
            )
        
        if blocked_count > 0:
            self.message_user(
                request,
                f"No se pudo reducir el almacenamiento de {blocked_count} organizaciones por exceder el uso actual.",
                messages.WARNING
            )
    
    reduce_extra_storage.short_description = "Reducir almacenamiento extra seguro"
    
    def add_extra_storage(self, request, queryset):
        """Agregar 10 GB de almacenamiento extra a organizaciones seleccionadas"""
        updated = 0
        
        for org in queryset:
            org.extra_storage_gb += 10
            org.save()
            updated += 1
        
        self.message_user(
            request,
            f"Se agregaron 10 GB extra a {updated} organizaciones.",
            messages.SUCCESS
        )
    
    add_extra_storage.short_description = "Agregar 10 GB extra"
    
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
    
    def save_model(self, request, obj, form, change):
        """
        Hook para guardar el modelo con logging estructurado.
        """
        try:
            if change:
                # Es una actualización - capturar cambios
                changes = []
                
                tracked_fields = {
                    'name': 'Nombre',
                    'is_active': 'Estado activo',
                    'email': 'Email'
                }
                
                try:
                    original = Client.objects.get(pk=obj.pk)
                    
                    for field_name, field_label in tracked_fields.items():
                        old_value = getattr(original, field_name)
                        new_value = getattr(obj, field_name)
                        
                        if old_value != new_value:
                            changes.append({
                                'field': field_name,
                                'field_label': field_label,
                                'old': old_value,
                                'new': new_value
                            })
                except Client.DoesNotExist:
                    change = False
            
            # Guardar el objeto
            super().save_model(request, obj, form, change)
            
            # Logging estructurado
            if change and changes:
                # CLIENT_UPDATED
                log_info(
                    event='CLIENT_UPDATED',
                    message=f"Cliente '{obj.name}' actualizado con {len(changes)} cambio(s)",
                    logger_name='apps.orgs',
                    client_id=obj.id,
                    client_name=obj.name,
                    organization_id=obj.organization.id if obj.organization else None,
                    organization_name=obj.organization.name if obj.organization else None,
                    changes=changes,
                    updated_by=request.user.email if request.user else 'Sistema'
                )
                
                changes_text = ', '.join([f"{c['field_label']}" for c in changes])
                messages.success(
                    request,
                    f"Cliente '{obj.name}' actualizado exitosamente. Cambios: {changes_text}"
                )
            else:
                # CLIENT_CREATED
                log_info(
                    event='CLIENT_CREATED',
                    message=f"Nuevo cliente creado: '{obj.name}'",
                    logger_name='apps.orgs',
                    client_id=obj.id,
                    client_name=obj.name,
                    organization_id=obj.organization.id if obj.organization else None,
                    organization_name=obj.organization.name if obj.organization else None,
                    email=obj.email,
                    is_active=obj.is_active,
                    created_by=request.user.email if request.user else 'Sistema'
                )
                
                messages.success(
                    request,
                    f"Cliente '{obj.name}' creado exitosamente."
                )
                
        except Exception as e:
            log_error(
                event='CLIENT_SAVE_FAILED',
                error_code='CLI001',
                error_message=str(e),
                logger_name='apps.orgs',
                client_name=getattr(obj, 'name', 'Desconocido'),
                action='update' if change else 'create',
                user_email=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al {'actualizar' if change else 'crear'} el cliente: {str(e)}"
            )
            
            raise
    
    def delete_model(self, request, obj):
        """
        Hook para eliminar el modelo con logging estructurado.
        """
        client_name = obj.name
        client_id = obj.id
        org_name = obj.organization.name if obj.organization else 'Sin organización'
        org_id = obj.organization.id if obj.organization else None
        
        try:
            log_info(
                event='CLIENT_DELETED',
                message=f"Cliente '{client_name}' eliminado",
                logger_name='apps.orgs',
                client_id=client_id,
                client_name=client_name,
                organization_id=org_id,
                organization_name=org_name,
                deleted_by=request.user.email if request.user else 'Sistema'
            )
            
            super().delete_model(request, obj)
            
            messages.success(
                request,
                f"Cliente '{client_name}' eliminado exitosamente."
            )
            
        except Exception as e:
            log_error(
                event='CLIENT_DELETE_FAILED',
                error_code='CLI002',
                error_message=str(e),
                logger_name='apps.orgs',
                client_id=client_id,
                client_name=client_name,
                deleted_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al eliminar el cliente '{client_name}': {str(e)}"
            )
            
            raise
