from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db import models
from .models import Project, Phase, Task, PhaseTemplate
from import_export import resources
from import_export.admin import ImportExportModelAdmin


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
            '<div>✅ <strong>{}</strong> completadas</div>'
            '<div>🔄 <strong>{}</strong> en progreso</div>'
            '<div>⏳ <strong>{}</strong> pendientes</div>'
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
                '<div style="margin-bottom: 4px;">📝 <strong>{}</strong> - {}</div>',
                task.title[:30] + '...' if len(task.title) > 30 else task.title,
                task.get_status_display()
            )
        activity_html += '</div>'
        
        return format_html(activity_html)
    get_recent_activity.short_description = 'Actividad Reciente'
    
    def duplicate_projects(self, request, queryset):
        """Duplicar proyectos seleccionados."""
        duplicated_count = 0
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
            except Exception as e:
                self.message_user(
                    request,
                    f"Error duplicando {project.name}: {str(e)}",
                    messages.ERROR
                )
        
        if duplicated_count > 0:
            self.message_user(
                request,
                f"✅ Se duplicaron {duplicated_count} proyectos correctamente.",
                messages.SUCCESS
            )
    duplicate_projects.short_description = "📋 Duplicar proyectos seleccionados"
    
    def generate_project_report(self, request, queryset):
        """Generar reporte de proyectos."""
        # Esta sería una funcionalidad para generar reportes
        project_count = queryset.count()
        self.message_user(
            request,
            f"📊 Se ha generado un reporte para {project_count} proyecto(s). "
            "Funcionalidad de reporte completa próximamente.",
            messages.INFO
        )
    generate_project_report.short_description = "📊 Generar reporte de proyectos"

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
    
    def mark_as_completed(self, request, queryset):
        """Marcar fases como completadas."""
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f"✅ Se marcaron {updated} fases como completadas.", messages.SUCCESS)
    mark_as_completed.short_description = "✅ Marcar como completadas"
    
    def mark_as_in_progress(self, request, queryset):
        """Marcar fases como en progreso."""
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"🔄 Se marcaron {updated} fases como en progreso.", messages.SUCCESS)
    mark_as_in_progress.short_description = "🔄 Marcar como en progreso"


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
    
    def mark_as_completed(self, request, queryset):
        """Marcar tareas como completadas."""
        updated = queryset.update(status='DONE')
        self.message_user(request, f"✅ Se marcaron {updated} tareas como completadas.", messages.SUCCESS)
    mark_as_completed.short_description = "✅ Marcar como completadas"
    
    def mark_as_in_progress(self, request, queryset):
        """Marcar tareas como en progreso."""
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"🔄 Se marcaron {updated} tareas como en progreso.", messages.SUCCESS)
    mark_as_in_progress.short_description = "🔄 Marcar como en progreso"
    
    def mark_as_pending(self, request, queryset):
        """Marcar tareas como pendientes."""
        updated = queryset.update(status='TODO')
        self.message_user(request, f"⏳ Se marcaron {updated} tareas como pendientes.", messages.SUCCESS)
    mark_as_pending.short_description = "⏳ Marcar como pendientes"
    
    def assign_to_me(self, request, queryset):
        """Asignar tareas al usuario actual."""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f"👤 Se asignaron {updated} tareas a tu usuario.", messages.SUCCESS)
    assign_to_me.short_description = "👤 Asignarme estas tareas"


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
