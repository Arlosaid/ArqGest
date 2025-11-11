from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db import models
from .models import Project, Phase, Task, PhaseTemplate
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from core.structured_logging import log_info, log_error


# --- Recursos para Import/Export ---

class ProjectResource(resources.ModelResource):
    """Resource para exportar proyectos con manejo seguro de relaciones."""
    
    def dehydrate_organization__name(self, project):
        """Manejar proyectos sin organización (no debería pasar con CASCADE, pero por seguridad)."""
        try:
            if project.organization:
                return project.organization.name
            return 'Sin organización'
        except Exception:
            return 'Sin organización'
    
    def dehydrate_client__name(self, project):
        """Manejar proyectos sin cliente."""
        try:
            if project.client:
                return project.client.name
            return 'Sin cliente'
        except Exception:
            return 'Sin cliente'
    
    def dehydrate_owner__email(self, project):
        """Manejar proyectos sin propietario (no debería pasar con CASCADE, pero por seguridad)."""
        try:
            if project.owner:
                return project.owner.email
            return 'Sin propietario'
        except Exception:
            return 'Sin propietario'
    
    class Meta:
        model = Project
        fields = ('id', 'name', 'organization__name', 'client__name', 'owner__email', 'created_at')
        export_order = fields


class TaskResource(resources.ModelResource):
    def dehydrate_assigned_to__email(self, task):
        """Manejar casos donde assigned_to es None"""
        return task.assigned_to.email if task.assigned_to else 'Sin asignar'
    
    class Meta:
        model = Task
        fields = ('id', 'title', 'phase__name', 'phase__project__name', 'assigned_to__email', 
                 'status', 'priority', 'due_date', 'created_at')
        export_order = fields


# --- Inlines ---

class TaskInline(admin.TabularInline):
    """Inline para mostrar Tareas dentro de una Fase."""
    model = Task
    extra = 0
    fields = ('title', 'assigned_to', 'get_status_display', 'get_priority_display', 'due_date')
    readonly_fields = ('get_status_display', 'get_priority_display')
    show_change_link = True
    verbose_name = "Tarea"
    verbose_name_plural = "Tareas en esta Fase"
    
    def get_status_display(self, obj):
        """Mostrar estado con colores."""
        if not obj.pk:  # Para formularios vacíos
            return ''
        status_colors = {
            'TODO': '#FFA500',
            'IN_PROGRESS': '#2196F3', 
            'DONE': '#4CAF50',
            'PAUSED': '#FF5722'
        }
        color = status_colors.get(obj.status, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Estado'
    
    def get_priority_display(self, obj):
        """Mostrar prioridad con iconos."""
        if not obj.pk:
            return ''
        priority_icons = {
            'LOW': '🟢',
            'MEDIUM': '🟡', 
            'HIGH': '🟠'
        }
        icon = priority_icons.get(obj.priority, '⚪')
        return format_html('{} {}', icon, obj.get_priority_display())
    get_priority_display.short_description = 'Prioridad'

    def has_add_permission(self, request, obj=None):
        return False


class PhaseInline(admin.TabularInline):
    """Inline para mostrar Fases dentro de un Proyecto."""
    model = Phase
    extra = 0
    fields = ('name', 'order', 'get_status_display', 'get_task_count')
    readonly_fields = ('get_status_display', 'get_task_count')
    show_change_link = True
    ordering = ('order',)
    verbose_name = "Fase"
    verbose_name_plural = "Fases del Proyecto"
    
    def get_status_display(self, obj):
        """Mostrar estado de la fase con colores."""
        if not obj.pk:
            return ''
        status_colors = {
            'PENDING': '#999',
            'IN_PROGRESS': '#2196F3',
            'COMPLETED': '#4CAF50'
        }
        color = status_colors.get(obj.status, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Estado'
    
    def get_task_count(self, obj):
        """Mostrar contador de tareas."""
        if not obj.pk:
            return ''
        count = obj.tasks.count()
        completed = obj.tasks.filter(status='completed').count()
        return format_html('{}/{} tareas', completed, count)
    get_task_count.short_description = 'Progreso'

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    """Administración avanzada de proyectos con herramientas de gestión."""
    resource_class = ProjectResource
    list_display = ('name', 'get_organization_link', 'get_client_link', 'get_owner_info', 
                   'get_phase_progress', 'get_task_summary', 'created_at')
    list_filter = ('organization__name', 'client__name', 'created_at')
    search_fields = ('name', 'client__name', 'owner__email', 'organization__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'get_phase_progress', 'get_task_summary', 'get_recent_activity')
    inlines = [PhaseInline]
    actions = ['duplicate_projects', 'generate_project_report']
    
    fieldsets = (
        ('Información del Proyecto', {
            'fields': ('name',)
        }),
        ('Asignaciones', {
            'fields': ('organization', 'client', 'owner'),
            'description': 'Organización responsable, cliente asociado y propietario del proyecto.'
        }),
        ('Progreso y Estadísticas', {
            'fields': ('get_phase_progress', 'get_task_summary', 'get_recent_activity'),
            'classes': ('collapse',),
            'description': 'Información de progreso y actividad reciente del proyecto.'
        }),
        ('Información del Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimizar consultas y añadir estadísticas."""
        return super().get_queryset(request).select_related(
            'organization', 'client', 'owner'
        ).prefetch_related('phases__tasks')
    
    def get_organization_link(self, obj):
        """Enlace a la organización."""
        try:
            if obj.organization:
                org_url = reverse('admin:orgs_organization_change', args=[obj.organization.pk])
                return format_html('<a href="{}">{}</a>', org_url, obj.organization.name)
            return format_html('<span style="color: #999;">Sin organización</span>')
        except Exception:
            return format_html('<span style="color: #999;">Error al cargar</span>')
    get_organization_link.short_description = 'Organización'
    get_organization_link.admin_order_field = 'organization__name'
    
    def get_client_link(self, obj):
        """Enlace al cliente."""
        try:
            if obj.client:
                client_url = reverse('admin:orgs_client_change', args=[obj.client.pk])
                return format_html('<a href="{}">{}</a>', client_url, obj.client.name)
            return format_html('<span style="color: #999;">Sin cliente</span>')
        except Exception:
            return format_html('<span style="color: #999;">Error al cargar</span>')
    get_client_link.short_description = 'Cliente'
    get_client_link.admin_order_field = 'client__name'
    
    def get_owner_info(self, obj):
        """Información del propietario con enlace."""
        try:
            if obj.owner:
                user_url = reverse('admin:accounts_user_change', args=[obj.owner.pk])
                return format_html(
                    '<a href="{}" style="text-decoration: none;">'
                    '<strong>{}</strong><br>'
                    '<small style="color: #666;">{}</small>'
                    '</a>',
                    user_url,
                    obj.owner.get_full_name() or obj.owner.email,
                    obj.owner.email
                )
            return format_html('<span style="color: #999;">Sin propietario</span>')
        except Exception:
            return format_html('<span style="color: #999;">Error al cargar</span>')
    get_owner_info.short_description = 'Propietario'
    get_owner_info.admin_order_field = 'owner__first_name'
    
    def get_phase_progress(self, obj):
        """Progreso de las fases."""
        phases = obj.phases.all()
        if not phases:
            return format_html('<span style="color: #999;">Sin fases</span>')
        
        total = phases.count()
        completed = phases.filter(status='completed').count()
        in_progress = phases.filter(status='in_progress').count()
        
        progress_percentage = (completed / total * 100) if total > 0 else 0
        
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="background: #f0f0f0; border-radius: 10px; width: 100px; height: 20px; overflow: hidden;">'
            '<div style="background: #4CAF50; height: 100%; width: {}%; transition: width 0.3s;"></div>'
            '</div>'
            '<span style="font-size: 12px; color: #666;">{}/{} fases ({:.0f}%)</span>'
            '</div>',
            progress_percentage,
            completed, total, progress_percentage
        )
    get_phase_progress.short_description = 'Progreso de Fases'
    
    def get_task_summary(self, obj):
        """Resumen de tareas del proyecto."""
        # Contar tareas a través de las fases
        all_tasks = Task.objects.filter(phase__project=obj)
        total_tasks = all_tasks.count()
        
        if total_tasks == 0:
            return format_html('<span style="color: #999;">Sin tareas</span>')
        
        completed_tasks = all_tasks.filter(status='completed').count()
        in_progress_tasks = all_tasks.filter(status='in_progress').count()
        pending_tasks = all_tasks.filter(status='pending').count()
        
        return format_html(
            '<div style="font-size: 12px;">'
            '<div>DONE: <strong>{}</strong></div>'
            '<div>IN_PROG: <strong>{}</strong></div>'
            '<div>PENDING: <strong>{}</strong></div>'
            '</div>',
            completed_tasks, in_progress_tasks, pending_tasks
        )
    get_task_summary.short_description = 'Resumen de Tareas'
    
    def get_recent_activity(self, obj):
        """Actividad reciente del proyecto."""
        # Obtener las tareas más recientes
        recent_tasks = Task.objects.filter(phase__project=obj).order_by('-updated_at')[:3]
        
        if not recent_tasks:
            return format_html('<span style="color: #999;">Sin actividad reciente</span>')
        
        activity_html = '<div style="font-size: 12px;">'
        for task in recent_tasks:
            activity_html += format_html(
                '<div style="margin-bottom: 4px;"><strong>{}</strong> - {}</div>',
                task.title[:30] + '...' if len(task.title) > 30 else task.title,
                task.get_status_display()
            )
        activity_html += '</div>'
        
        return format_html(activity_html)
    get_recent_activity.short_description = 'Actividad Reciente'
    
    def save_model(self, request, obj, form, change):
        """Hook para guardar el modelo con logging estructurado."""
        try:
            if change:
                # Es una actualización - capturar cambios
                changes = []
                
                tracked_fields = {
                    'name': 'Nombre',
                    'organization': 'Organización',
                    'client': 'Cliente',
                    'owner': 'Propietario'
                }
                
                try:
                    original = Project.objects.get(pk=obj.pk)
                    
                    for field_name, field_label in tracked_fields.items():
                        old_value = getattr(original, field_name)
                        new_value = getattr(obj, field_name)
                        
                        if old_value != new_value:
                            # Formatear valores para logging
                            if field_name == 'organization':
                                old_val = old_value.name if old_value else 'Sin organización'
                                new_val = new_value.name if new_value else 'Sin organización'
                            elif field_name == 'client':
                                old_val = old_value.name if old_value else 'Sin cliente'
                                new_val = new_value.name if new_value else 'Sin cliente'
                            elif field_name == 'owner':
                                old_val = old_value.email if old_value else 'Sin propietario'
                                new_val = new_value.email if new_value else 'Sin propietario'
                            else:
                                old_val = str(old_value)
                                new_val = str(new_value)
                            
                            changes.append({
                                'field': field_name,
                                'field_label': field_label,
                                'old': old_val,
                                'new': new_val
                            })
                except Project.DoesNotExist:
                    change = False
            
            # Guardar el objeto
            super().save_model(request, obj, form, change)
            
            # Logging estructurado
            if change and changes:
                log_info(
                    event='PROJECT_UPDATED',
                    message=f"Proyecto '{obj.name}' actualizado con {len(changes)} cambio(s)",
                    logger_name='apps.projects',
                    project_id=obj.id,
                    project_name=obj.name,
                    organization_id=obj.organization.id if obj.organization else None,
                    organization_name=obj.organization.name if obj.organization else 'Sin organización',
                    changes=changes,
                    updated_by=request.user.email if request.user else 'Sistema'
                )
                
                # Mensaje para el admin
                changes_text = ', '.join([f"{c['field_label']}" for c in changes])
                messages.success(
                    request,
                    f"Proyecto '{obj.name}' actualizado exitosamente. Cambios: {changes_text}"
                )
            elif not change:
                # Creación de proyecto
                log_info(
                    event='PROJECT_CREATED',
                    message=f"Proyecto '{obj.name}' creado exitosamente",
                    logger_name='apps.projects',
                    project_id=obj.id,
                    project_name=obj.name,
                    organization_id=obj.organization.id if obj.organization else None,
                    organization_name=obj.organization.name if obj.organization else 'Sin organización',
                    created_by=request.user.email if request.user else 'Sistema'
                )
        
        except Exception as e:
            log_error(
                event='PROJECT_SAVE_FAILED',
                error_code='PROJ001',
                error_message=str(e),
                logger_name='apps.projects',
                project_name=getattr(obj, 'name', 'Desconocido'),
                action='create' if not change else 'update',
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al {'crear' if not change else 'actualizar'} el proyecto: {str(e)}"
            )
            
            raise
    
    def duplicate_projects(self, request, queryset):
        """Duplicar proyectos seleccionados con logging estructurado."""
        duplicated_count = 0
        failed_count = 0
        duplicated_names = []
        failed_projects = []
        
        for project in queryset:
            try:
                # Crear copia del proyecto
                new_project = Project.objects.create(
                    name=f"{project.name} (Copia)",
                    organization=project.organization,
                    client=project.client,
                    owner=project.owner
                )
                duplicated_count += 1
                duplicated_names.append(new_project.name)
                
                # Log de éxito individual
                log_info(
                    event='PROJECT_DUPLICATED',
                    message=f"Proyecto '{project.name}' duplicado como '{new_project.name}'",
                    logger_name='apps.projects',
                    original_project_id=project.id,
                    new_project_id=new_project.id,
                    duplicated_by=request.user.email if request.user else 'Sistema'
                )
                
            except Exception as e:
                failed_count += 1
                failed_projects.append({'name': project.name, 'error': str(e)})
                
                # Log del error
                log_error(
                    event='PROJECT_DUPLICATE_FAILED',
                    error_code='PROJ_DUP_001',
                    error_message=str(e),
                    logger_name='apps.projects',
                    project_id=project.id,
                    project_name=project.name,
                    performed_by=request.user.email if request.user else 'Sistema'
                )
                
                self.message_user(
                    request,
                    f"Error duplicando '{project.name}': {str(e)[:100]}",
                    messages.ERROR
                )
        
        # Mensajes finales
        if duplicated_count > 0:
            self.message_user(
                request,
                f"✅ Se duplicaron {duplicated_count} proyecto(s) correctamente: {', '.join(duplicated_names[:3])}" +
                (f" y {len(duplicated_names)-3} más" if len(duplicated_names) > 3 else ""),
                messages.SUCCESS
            )
        
        if failed_count > 0:
            self.message_user(
                request,
                f"❌ Fallaron {failed_count} proyecto(s). Revisa los logs para más detalles.",
                messages.WARNING
            )
    duplicate_projects.short_description = "Duplicar proyectos seleccionados"
    
    def generate_project_report(self, request, queryset):
        """Generar reporte de proyectos."""
        # Esta sería una funcionalidad para generar reportes
        project_count = queryset.count()
        self.message_user(
            request,
            f"Se ha generado un reporte para {project_count} proyecto(s). "
            "Funcionalidad de reporte completa próximamente.",
            messages.INFO
        )
    generate_project_report.short_description = "Generar reporte de proyectos"

@admin.register(Phase)
class PhaseAdmin(ImportExportModelAdmin):
    """Administración de fases con vista detallada de tareas."""
    list_display = ('name', 'get_project_link', 'get_status_display', 'order', 
                   'get_task_progress', 'created_at')
    list_filter = ('status', 'project__organization__name', 'project__name', 'created_at')
    search_fields = ('name', 'notes', 'project__name', 'project__organization__name')
    ordering = ('project__name', 'order')
    readonly_fields = ('created_at', 'get_task_progress', 'get_project_link')
    inlines = [TaskInline]
    actions = ['mark_as_completed', 'mark_as_in_progress']
    
    fieldsets = (
        ('Información de la Fase', {
            'fields': ('name', 'notes', 'order', 'status')
        }),
        ('Proyecto Asociado', {
            'fields': ('project', 'get_project_link'),
            'description': 'Proyecto al que pertenece esta fase.'
        }),
        ('Progreso y Estadísticas', {
            'fields': ('get_task_progress',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'project__organization'
        ).prefetch_related('tasks')
    
    def get_project_link(self, obj):
        """Enlace al proyecto."""
        project_url = reverse('admin:projects_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', project_url, obj.project.name)
    get_project_link.short_description = 'Proyecto'
    get_project_link.admin_order_field = 'project__name'
    
    def get_status_display(self, obj):
        """Estado con colores."""
        status_colors = {
            'not_started': '#999',
            'in_progress': '#2196F3',
            'completed': '#4CAF50',
            'on_hold': '#FF5722'
        }
        color = status_colors.get(obj.status, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Estado'
    get_status_display.admin_order_field = 'status'
    
    def get_task_progress(self, obj):
        """Progreso de tareas en la fase."""
        tasks = obj.tasks.all()
        if not tasks:
            return format_html('<span style="color: #999;">Sin tareas</span>')
        
        total = tasks.count()
        completed = tasks.filter(status='DONE').count()
        progress_percentage = (completed / total * 100) if total > 0 else 0
        
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="background: #f0f0f0; border-radius: 10px; width: 80px; height: 16px; overflow: hidden;">'
            '<div style="background: #4CAF50; height: 100%; width: {}%;"></div>'
            '</div>'
            '<span style="font-size: 11px;">{}/{} ({:.0f}%)</span>'
            '</div>',
            progress_percentage, completed, total, progress_percentage
        )
    get_task_progress.short_description = 'Progreso de Tareas'
    
    def save_model(self, request, obj, form, change):
        """Hook para guardar el modelo con logging estructurado."""
        try:
            if change:
                # Es una actualización - capturar cambios
                changes = []
                
                tracked_fields = {
                    'name': 'Nombre',
                    'status': 'Estado',
                    'order': 'Orden',
                    'notes': 'Notas'
                }
                
                try:
                    original = Phase.objects.get(pk=obj.pk)
                    
                    for field_name, field_label in tracked_fields.items():
                        old_value = getattr(original, field_name)
                        new_value = getattr(obj, field_name)
                        
                        if old_value != new_value:
                            # Formatear valores para logging
                            if field_name == 'status':
                                old_val = original.get_status_display()
                                new_val = obj.get_status_display()
                            else:
                                old_val = str(old_value) if old_value else ''
                                new_val = str(new_value) if new_value else ''
                            
                            changes.append({
                                'field': field_name,
                                'field_label': field_label,
                                'old': old_val,
                                'new': new_val
                            })
                except Phase.DoesNotExist:
                    change = False
            
            # Guardar el objeto
            super().save_model(request, obj, form, change)
            
            # Logging estructurado
            if change and changes:
                log_info(
                    event='PHASE_UPDATED',
                    message=f"Fase '{obj.name}' actualizada con {len(changes)} cambio(s)",
                    logger_name='apps.projects',
                    phase_id=obj.id,
                    phase_name=obj.name,
                    project_id=obj.project.id,
                    project_name=obj.project.name,
                    changes=changes,
                    updated_by=request.user.email if request.user else 'Sistema'
                )
                
                # Mensaje para el admin
                changes_text = ', '.join([f"{c['field_label']}" for c in changes])
                messages.success(
                    request,
                    f"Fase '{obj.name}' actualizada exitosamente. Cambios: {changes_text}"
                )
            elif not change:
                # Creación de fase
                log_info(
                    event='PHASE_CREATED',
                    message=f"Fase '{obj.name}' creada exitosamente",
                    logger_name='apps.projects',
                    phase_id=obj.id,
                    phase_name=obj.name,
                    project_id=obj.project.id,
                    project_name=obj.project.name,
                    created_by=request.user.email if request.user else 'Sistema'
                )
        
        except Exception as e:
            log_error(
                event='PHASE_SAVE_FAILED',
                error_code='PHASE001',
                error_message=str(e),
                logger_name='apps.projects',
                phase_name=getattr(obj, 'name', 'Desconocido'),
                action='create' if not change else 'update',
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al {'crear' if not change else 'actualizar'} la fase: {str(e)}"
            )
            
            raise
    
    def mark_as_completed(self, request, queryset):
        """Marcar fases como completadas con logging."""
        phase_count = queryset.count()
        phase_ids = list(queryset.values_list('id', flat=True))
        phase_names = list(queryset.values_list('name', flat=True))
        
        try:
            updated = queryset.update(status='completed')
            
            # Log de éxito
            log_info(
                event='PHASES_MARKED_COMPLETED',
                message=f"{updated} fases marcadas como completadas",
                logger_name='apps.projects',
                phase_ids=phase_ids,
                phase_names=phase_names[:5],
                updated_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request, 
                f"Se marcaron {updated} fases como completadas.",
                messages.SUCCESS
            )
        except Exception as e:
            log_error(
                event='PHASES_MARK_COMPLETED_FAILED',
                error_code='PHASE_STATUS_001',
                error_message=str(e),
                logger_name='apps.projects',
                phase_count=phase_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al marcar fases como completadas: {str(e)}",
                messages.ERROR
            )
    mark_as_completed.short_description = "Marcar como completadas"
    
    def mark_as_in_progress(self, request, queryset):
        """Marcar fases como en progreso con logging."""
        phase_count = queryset.count()
        phase_ids = list(queryset.values_list('id', flat=True))
        phase_names = list(queryset.values_list('name', flat=True))
        
        try:
            updated = queryset.update(status='in_progress')
            
            # Log de éxito
            log_info(
                event='PHASES_MARKED_IN_PROGRESS',
                message=f"{updated} fases marcadas como en progreso",
                logger_name='apps.projects',
                phase_ids=phase_ids,
                phase_names=phase_names[:5],
                updated_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request, 
                f"Se marcaron {updated} fases como en progreso.",
                messages.SUCCESS
            )
        except Exception as e:
            log_error(
                event='PHASES_MARK_IN_PROGRESS_FAILED',
                error_code='PHASE_STATUS_002',
                error_message=str(e),
                logger_name='apps.projects',
                phase_count=phase_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al marcar fases como en progreso: {str(e)}",
                messages.ERROR
            )
    mark_as_in_progress.short_description = "Marcar como en progreso"


@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):
    """Administración detallada de tareas con herramientas de gestión."""
    resource_class = TaskResource
    list_display = ('title', 'get_phase_link', 'get_project_link', 'get_assigned_to_info', 
                   'get_status_display', 'get_priority_display', 'due_date')
    list_filter = ('status', 'priority', 'assigned_to', 'phase__project__organization__name', 
                  'phase__project__name', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'phase__name', 'phase__project__name',
                    'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'get_project_link', 'get_phase_link')
    actions = ['mark_as_completed', 'mark_as_in_progress', 'mark_as_pending', 'assign_to_me']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Información de la Tarea', {
            'fields': ('title', 'description', 'status', 'priority')
        }),
        ('Asignación', {
            'fields': ('phase', 'assigned_to', 'due_date'),
            'description': 'Fase, responsable y fecha límite de la tarea.'
        }),
        ('Enlaces Relacionados', {
            'fields': ('get_phase_link', 'get_project_link'),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'phase__project__organization', 'assigned_to'
        )
    
    def get_phase_link(self, obj):
        """Enlace a la fase."""
        phase_url = reverse('admin:projects_phase_change', args=[obj.phase.pk])
        return format_html('<a href="{}">{}</a>', phase_url, obj.phase.name)
    get_phase_link.short_description = 'Fase'
    get_phase_link.admin_order_field = 'phase__name'
    
    def get_project_link(self, obj):
        """Enlace al proyecto."""
        project_url = reverse('admin:projects_project_change', args=[obj.phase.project.pk])
        return format_html('<a href="{}">{}</a>', project_url, obj.phase.project.name)
    get_project_link.short_description = 'Proyecto'
    get_project_link.admin_order_field = 'phase__project__name'
    
    def get_assigned_to_info(self, obj):
        """Información del asignado."""
        if obj.assigned_to:
            user_url = reverse('admin:accounts_user_change', args=[obj.assigned_to.pk])
            return format_html(
                '<a href="{}" style="text-decoration: none;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small>'
                '</a>',
                user_url,
                obj.assigned_to.get_full_name() or obj.assigned_to.email,
                obj.assigned_to.email
            )
        return format_html('<span style="color: #999;">Sin asignar</span>')
    get_assigned_to_info.short_description = 'Asignado a'
    get_assigned_to_info.admin_order_field = 'assigned_to__first_name'
    
    def get_status_display(self, obj):
        """Estado con colores."""
        status_colors = {
            'TODO': '#FFA500',
            'IN_PROGRESS': '#2196F3',
            'DONE': '#4CAF50',
            'PAUSED': '#FF5722'
        }
        color = status_colors.get(obj.status, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Estado'
    get_status_display.admin_order_field = 'status'
    
    def get_priority_display(self, obj):
        """Prioridad con iconos."""
        priority_icons = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠'
        }
        icon = priority_icons.get(obj.priority, '⚪')
        return format_html('{} {}', icon, obj.get_priority_display())
    get_priority_display.short_description = 'Prioridad'
    get_priority_display.admin_order_field = 'priority'
    
    def save_model(self, request, obj, form, change):
        """Hook para guardar el modelo con logging estructurado."""
        try:
            if change:
                # Es una actualización - capturar cambios
                changes = []
                
                tracked_fields = {
                    'title': 'Título',
                    'status': 'Estado',
                    'priority': 'Prioridad',
                    'assigned_to': 'Asignado a',
                    'due_date': 'Fecha límite',
                    'description': 'Descripción'
                }
                
                try:
                    original = Task.objects.get(pk=obj.pk)
                    
                    for field_name, field_label in tracked_fields.items():
                        old_value = getattr(original, field_name)
                        new_value = getattr(obj, field_name)
                        
                        if old_value != new_value:
                            # Formatear valores para logging
                            if field_name == 'status':
                                old_val = original.get_status_display()
                                new_val = obj.get_status_display()
                            elif field_name == 'priority':
                                old_val = original.get_priority_display()
                                new_val = obj.get_priority_display()
                            elif field_name == 'assigned_to':
                                old_val = old_value.email if old_value else 'Sin asignar'
                                new_val = new_value.email if new_value else 'Sin asignar'
                            elif field_name == 'due_date':
                                old_val = old_value.strftime('%Y-%m-%d') if old_value else 'Sin fecha'
                                new_val = new_value.strftime('%Y-%m-%d') if new_value else 'Sin fecha'
                            else:
                                old_val = str(old_value) if old_value else ''
                                new_val = str(new_value) if new_value else ''
                            
                            changes.append({
                                'field': field_name,
                                'field_label': field_label,
                                'old': old_val,
                                'new': new_val
                            })
                except Task.DoesNotExist:
                    change = False
            
            # Guardar el objeto
            super().save_model(request, obj, form, change)
            
            # Logging estructurado
            if change and changes:
                log_info(
                    event='TASK_UPDATED',
                    message=f"Tarea '{obj.title}' actualizada con {len(changes)} cambio(s)",
                    logger_name='apps.projects',
                    task_id=obj.id,
                    task_title=obj.title,
                    phase_id=obj.phase.id,
                    phase_name=obj.phase.name,
                    project_id=obj.phase.project.id,
                    project_name=obj.phase.project.name,
                    changes=changes,
                    updated_by=request.user.email if request.user else 'Sistema'
                )
                
                # Mensaje para el admin
                changes_text = ', '.join([f"{c['field_label']}" for c in changes])
                messages.success(
                    request,
                    f"Tarea '{obj.title}' actualizada exitosamente. Cambios: {changes_text}"
                )
            elif not change:
                # Creación de tarea
                log_info(
                    event='TASK_CREATED',
                    message=f"Tarea '{obj.title}' creada exitosamente",
                    logger_name='apps.projects',
                    task_id=obj.id,
                    task_title=obj.title,
                    phase_id=obj.phase.id,
                    phase_name=obj.phase.name,
                    project_id=obj.phase.project.id,
                    project_name=obj.phase.project.name,
                    created_by=request.user.email if request.user else 'Sistema'
                )
        
        except Exception as e:
            log_error(
                event='TASK_SAVE_FAILED',
                error_code='TASK001',
                error_message=str(e),
                logger_name='apps.projects',
                task_title=getattr(obj, 'title', 'Desconocido'),
                action='create' if not change else 'update',
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al {'crear' if not change else 'actualizar'} la tarea: {str(e)}"
            )
            
            raise
    
    def mark_as_completed(self, request, queryset):
        """Marcar tareas como completadas con logging."""
        task_count = queryset.count()
        task_ids = list(queryset.values_list('id', flat=True))
        task_titles = list(queryset.values_list('title', flat=True))
        
        try:
            updated = queryset.update(status='DONE')
            
            # Log de éxito
            log_info(
                event='TASKS_MARKED_COMPLETED',
                message=f"{updated} tareas marcadas como completadas",
                logger_name='apps.projects',
                task_ids=task_ids,
                task_titles=task_titles[:5],
                updated_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request, 
                f"Se marcaron {updated} tareas como completadas.",
                messages.SUCCESS
            )
        except Exception as e:
            log_error(
                event='TASKS_MARK_COMPLETED_FAILED',
                error_code='TASK_STATUS_001',
                error_message=str(e),
                logger_name='apps.projects',
                task_count=task_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al marcar tareas como completadas: {str(e)}",
                messages.ERROR
            )
    mark_as_completed.short_description = "Marcar como completadas"
    
    def mark_as_in_progress(self, request, queryset):
        """Marcar tareas como en progreso con logging."""
        task_count = queryset.count()
        task_ids = list(queryset.values_list('id', flat=True))
        task_titles = list(queryset.values_list('title', flat=True))
        
        try:
            updated = queryset.update(status='IN_PROGRESS')
            
            # Log de éxito
            log_info(
                event='TASKS_MARKED_IN_PROGRESS',
                message=f"{updated} tareas marcadas como en progreso",
                logger_name='apps.projects',
                task_ids=task_ids,
                task_titles=task_titles[:5],
                updated_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request, 
                f"Se marcaron {updated} tareas como en progreso.",
                messages.SUCCESS
            )
        except Exception as e:
            log_error(
                event='TASKS_MARK_IN_PROGRESS_FAILED',
                error_code='TASK_STATUS_002',
                error_message=str(e),
                logger_name='apps.projects',
                task_count=task_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al marcar tareas como en progreso: {str(e)}",
                messages.ERROR
            )
    mark_as_in_progress.short_description = "Marcar como en progreso"
    
    def mark_as_pending(self, request, queryset):
        """Marcar tareas como pendientes con logging."""
        task_count = queryset.count()
        task_ids = list(queryset.values_list('id', flat=True))
        task_titles = list(queryset.values_list('title', flat=True))
        
        try:
            updated = queryset.update(status='TODO')
            
            # Log de éxito
            log_info(
                event='TASKS_MARKED_PENDING',
                message=f"{updated} tareas marcadas como pendientes",
                logger_name='apps.projects',
                task_ids=task_ids,
                task_titles=task_titles[:5],
                updated_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request, 
                f"Se marcaron {updated} tareas como pendientes.",
                messages.SUCCESS
            )
        except Exception as e:
            log_error(
                event='TASKS_MARK_PENDING_FAILED',
                error_code='TASK_STATUS_003',
                error_message=str(e),
                logger_name='apps.projects',
                task_count=task_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al marcar tareas como pendientes: {str(e)}",
                messages.ERROR
            )
    mark_as_pending.short_description = "Marcar como pendientes"
    
    def assign_to_me(self, request, queryset):
        """Asignar tareas al usuario actual con logging."""
        task_count = queryset.count()
        task_ids = list(queryset.values_list('id', flat=True))
        task_titles = list(queryset.values_list('title', flat=True))
        
        try:
            updated = queryset.update(assigned_to=request.user)
            
            # Log de éxito
            log_info(
                event='TASKS_ASSIGNED',
                message=f"{updated} tareas asignadas a {request.user.email}",
                logger_name='apps.projects',
                task_ids=task_ids,
                task_titles=task_titles[:5],
                assigned_to=request.user.email,
                assigned_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request, 
                f"Se asignaron {updated} tareas a tu usuario.",
                messages.SUCCESS
            )
        except Exception as e:
            log_error(
                event='TASKS_ASSIGN_FAILED',
                error_code='TASK_ASSIGN_001',
                error_message=str(e),
                logger_name='apps.projects',
                task_count=task_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al asignar tareas: {str(e)}",
                messages.ERROR
            )
    assign_to_me.short_description = "Asignarme estas tareas"


@admin.register(PhaseTemplate)
class PhaseTemplateAdmin(ImportExportModelAdmin):
    """Administración de plantillas de fases."""
    list_display = ('name', 'get_organization_link')
    list_filter = ('organization__name',)
    search_fields = ('name', 'description', 'organization__name')
    
    fieldsets = (
        ('Información de la Plantilla', {
            'fields': ('name', 'description', 'organization', 'phases')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')
    
    def get_organization_link(self, obj):
        """Enlace a la organización."""
        org_url = reverse('admin:orgs_organization_change', args=[obj.organization.pk])
        return format_html('<a href="{}">{}</a>', org_url, obj.organization.name)
    get_organization_link.short_description = 'Organización'
    get_organization_link.admin_order_field = 'organization__name'
