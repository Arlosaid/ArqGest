from django.urls import path
from .views import (
    ProjectListView,
    ProjectCreateView,
    ProjectDetailView,
    ProjectUpdateView,
    ProjectDeleteView,
    PhaseDetailView,
    project_kanban,
    project_statistics,
    phase_create,
    task_create,
    TaskListView,
    MyTaskListView,
    update_task_status,
    move_task,
    task_edit,
    task_detail,
    PhaseTemplateListView,
    PhaseTemplateCreateView,
    PhaseTemplateDetailView,
    PhaseTemplateUpdateView,
    PhaseTemplateDeleteView,
    task_delete,
    ProjectKanbanSelectorView,
)

app_name = 'projects'

urlpatterns = [
    # Proyectos principales
    path('', ProjectListView.as_view(), name='project-list'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    
    # Kanban y gestión de tareas (vista principal)
    path('<int:pk>/tasks/', project_kanban, name='project-kanban'),
    path('<int:pk>/kanban/', project_kanban, name='project-kanban-alt'),  # Alias para compatibilidad
    
    # Estadísticas del proyecto
    path('<int:pk>/statistics/', project_statistics, name='project-statistics'),
    
    # Gestión de tareas
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('my-tasks/', MyTaskListView.as_view(), name='my-task-list'),
    path('tasks/<int:pk>/', task_detail, name='task-detail'),
    path('tasks/<int:pk>/edit/', task_edit, name='task-edit'),
    path('tasks/<int:pk>/delete/', task_delete, name='task-delete'),
    path('tasks/<int:task_pk>/update_status/', update_task_status, name='update-task-status'),
    path('tasks/<int:task_pk>/move/', move_task, name='task-move'),
    
    # Gestión de fases
    path('<int:project_pk>/phases/<int:pk>/', PhaseDetailView.as_view(), name='phase-detail'),
    path('<int:project_pk>/phases/create/', phase_create, name='phase-create'),
    
    # Creación de tareas desde proyecto
    path('<int:project_pk>/tasks/create/', task_create, name='task-create'),
    
    # Plantillas de fases
    path('templates/', PhaseTemplateListView.as_view(), name='phasetemplate-list'),
    path('templates/new/', PhaseTemplateCreateView.as_view(), name='phasetemplate-create'),
    path('templates/<int:pk>/', PhaseTemplateDetailView.as_view(), name='phasetemplate-detail'),
    path('templates/<int:pk>/edit/', PhaseTemplateUpdateView.as_view(), name='phasetemplate-update'),
    path('templates/<int:pk>/delete/', PhaseTemplateDeleteView.as_view(), name='phasetemplate-delete'),
    path('kanban-selector/', ProjectKanbanSelectorView.as_view(), name='kanban-selector'),
]
