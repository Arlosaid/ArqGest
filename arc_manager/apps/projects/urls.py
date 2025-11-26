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
    get_project_stats,
    phase_create,
    check_phase_data,
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
    phase_files_paginated,
    project_tasks_paginated,
    ProjectPhasesEditView,
    ProjectToggleStatusView,
    # Finance module views
    FinanceDashboardView,
    ProjectFinanceDetailView,
    ProjectBudgetConfigView,
    PaymentCreateView,
    PaymentUpdateView,
    PaymentDeleteView,
)

app_name = 'projects'

urlpatterns = [
    # Proyectos principales
    path('', ProjectListView.as_view(), name='project-list'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('<int:pk>/stats/', get_project_stats, name='project-stats'),
    path('<int:pk>/toggle-status/', ProjectToggleStatusView.as_view(), name='project-toggle-status'),
    
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
    path('<int:pk>/phases/edit/', ProjectPhasesEditView.as_view(), name='project-phases-edit'),
    path('phases/<int:phase_id>/check-data/', check_phase_data, name='phase-check-data'),
    path('<int:project_id>/phases/<int:phase_id>/files/', phase_files_paginated, name='phase-files-paginated'),
    
    # Paginación AJAX de tareas
    path('<int:project_pk>/tasks/paginated/', project_tasks_paginated, name='project-tasks-paginated'),
    
    # Creación de tareas desde proyecto
    path('<int:project_pk>/tasks/create/', task_create, name='task-create'),
    
    # Plantillas de fases
    path('templates/', PhaseTemplateListView.as_view(), name='phasetemplate-list'),
    path('templates/new/', PhaseTemplateCreateView.as_view(), name='phasetemplate-create'),
    path('templates/<int:pk>/', PhaseTemplateDetailView.as_view(), name='phasetemplate-detail'),
    path('templates/<int:pk>/edit/', PhaseTemplateUpdateView.as_view(), name='phasetemplate-update'),
    path('templates/<int:pk>/delete/', PhaseTemplateDeleteView.as_view(), name='phasetemplate-delete'),
    path('kanban-selector/', ProjectKanbanSelectorView.as_view(), name='kanban-selector'),
    
    # Finance module URLs
    path('finance/', FinanceDashboardView.as_view(), name='finance-dashboard'),
    path('<int:pk>/finance/', ProjectFinanceDetailView.as_view(), name='finance-project-detail'),
    path('<int:pk>/budget/config/', ProjectBudgetConfigView.as_view(), name='budget-config'),
    path('<int:project_id>/payments/new/', PaymentCreateView.as_view(), name='payment-create'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment-edit'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment-delete'),
]
