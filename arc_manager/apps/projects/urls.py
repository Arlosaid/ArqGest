from django.urls import path
from .views import (
    ProjectListView,
    ProjectCreateView,
    ProjectDetailView,
    ProjectUpdateView,
    ProjectDeleteView,
    advance_project_phase,
    task_create,
    TaskListView,
    update_task_status,
)

app_name = 'projects'

urlpatterns = [
    path('', ProjectListView.as_view(), name='project-list'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/<int:task_pk>/update_status/', update_task_status, name='update-task-status'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('<int:pk>/advance-phase/', advance_project_phase, name='project-advance-phase'),
    # URL for creating a task within a project
    path('<int:project_pk>/tasks/create/', task_create, name='task-create'),
]
