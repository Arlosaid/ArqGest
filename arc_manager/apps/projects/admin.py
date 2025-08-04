from django.contrib import admin
from .models import Project, Phase, Task, ProjectFile, ProjectTemplate, PhaseTemplate

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'owner', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('name', 'client', 'owner__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'order', 'created_at')
    list_filter = ('status', 'project__name')
    search_fields = ('name', 'project__name')
    ordering = ('project', 'order')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'phase', 'assigned_to', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority', 'assigned_to', 'phase__project__name')
    search_fields = ('title', 'description', 'phase__name', 'phase__project__name')
    ordering = ('-created_at',)

@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'phase', 'uploaded_at')
    list_filter = ('phase__name', 'phase__project__name')
    search_fields = ('file__name',)
    ordering = ('-uploaded_at',)

class PhaseTemplateInline(admin.TabularInline):
    model = PhaseTemplate
    extra = 1  # Number of extra forms to display
    ordering = ('order',)

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    inlines = [PhaseTemplateInline]
