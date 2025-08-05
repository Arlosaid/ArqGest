from django.urls import path
from .views import (
    ProjectListView,
    ProjectCreateView,
    ProjectDetailView,
    ProjectKanbanView,  # Import the new Kanban view
    ProjectUpdateView,
    ProjectDeleteView,
    PhaseDetailView,
    task_create,
    TaskListView,
    MyTaskListView,
    update_task_status,
    move_task,
    task_edit,
)

app_name = 'projects'

urlpatterns = [
    path('', ProjectListView.as_view(), name='project-list'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/kanban/', ProjectKanbanView.as_view(), name='project-kanban'),  # New Kanban URL
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('my-tasks/', MyTaskListView.as_view(), name='my-task-list'),
    path('tasks/<int:pk>/edit/', task_edit, name='task-edit'),
    path('tasks/<int:task_pk>/update_status/', update_task_status, name='update-task-status'),
    path('tasks/<int:task_pk>/move/', move_task, name='task-move'),
    
    path('<int:project_pk>/phases/<int:pk>/', PhaseDetailView.as_view(), name='phase-detail'),
    path('<int:project_pk>/tasks/create/', task_create, name='task-create'),
]
