from django.contrib import admin
from .models import Project, Phase, Task, PhaseTemplate

class TaskInline(admin.TabularInline):
    """Inline para mostrar Tareas dentro de una Fase."""
    model = Task
    extra = 0  # No mostrar formularios de tareas vacíos por defecto
    fields = ('title', 'assigned_to', 'status', 'priority', 'due_date')
    readonly_fields = ('title', 'assigned_to', 'status', 'priority', 'due_date')
    show_change_link = True
    verbose_name = "Tarea"
    verbose_name_plural = "Tareas en esta Fase"

    def has_add_permission(self, request, obj=None):
        return False # No permitir añadir tareas desde aquí para mantener la UI limpia

class PhaseInline(admin.TabularInline):
    """Inline para mostrar Fases dentro de un Proyecto."""
    model = Phase
    extra = 0
    fields = ('name', 'order', 'status')
    readonly_fields = ('name', 'order', 'status')
    show_change_link = True
    ordering = ('order',)
    verbose_name = "Fase"
    verbose_name_plural = "Fases del Proyecto"

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'client', 'owner', 'created_at')
    list_filter = ('organization__name', 'client__name', 'owner__email', 'created_at')
    search_fields = ('name', 'client__name', 'owner__email', 'organization__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    inlines = [PhaseInline]
    
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Asignación', {'fields': ('organization', 'client', 'owner')}),
        ('Sistema', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'client', 'owner')

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'order', 'created_at')
    list_filter = ('status', 'project__organization__name', 'project__name')
    search_fields = ('name', 'project__name', 'project__organization__name')
    ordering = ('project__name', 'order')
    inlines = [TaskInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project__organization')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'phase', 'project_link', 'assigned_to', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority', 'assigned_to', 'phase__project__organization__name', 'phase__project__name')
    search_fields = ('title', 'description', 'phase__name', 'phase__project__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'project_link')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('phase__project', 'assigned_to')

    def project_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:projects_project_change", args=[obj.phase.project.id])
        return format_html('<a href="{}">{}</a>', link, obj.phase.project.name)
    project_link.short_description = 'Proyecto'

@admin.register(PhaseTemplate)
class PhaseTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')
    list_filter = ('organization__name',)
    search_fields = ('name', 'organization__name')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')
