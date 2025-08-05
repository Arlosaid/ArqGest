from django.urls import path
from .views import (
    ProjectListView,
    ProjectCreateView,
    ProjectDetailView,
    ProjectUpdateView,
    ProjectDeleteView,
    task_create,
    TaskListView,
    MyTaskListView,  # Renamed for clarity and added
    update_task_status,
    move_task,
    task_edit,
)

app_name = 'projects'

urlpatterns = [
    path('', ProjectListView.as_view(), name='project-list'),
    path('new/', ProjectCreateView.as_view(), name='project-create'),
    path('tasks/', TaskListView.as_view(), name='task-list'),  # This is a general task list
    path('my-tasks/', MyTaskListView.as_view(), name='my-task-list'),  # New view for personal tasks
    path('tasks/<int:pk>/edit/', task_edit, name='task-edit'),
    path('tasks/<int:task_pk>/update_status/', update_task_status, name='update-task-status'),
    path('tasks/<int:task_pk>/move/', move_task, name='task-move'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    # URL for creating a task within a project
    path('<int:project_pk>/tasks/create/', task_create, name='task-create'),
]
