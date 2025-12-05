from django.urls import path
from . import views, api

app_name = 'files'

urlpatterns = [
    # Ejemplo: /projects/1/phases/2/files/upload/
    path('projects/<int:project_id>/phases/<int:phase_id>/files/upload/', views.upload_file, name='upload_file'),
    # Upload con task_id: /projects/1/phases/2/tasks/5/files/upload/
    path('projects/<int:project_id>/phases/<int:phase_id>/tasks/<int:task_id>/files/upload/', views.upload_task_file, name='upload_task_file'),
    # Ejemplo: /files/3/delete/
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    # Presigned URL endpoints (opcional para R2/S3)
    path('projects/<int:project_id>/phases/<int:phase_id>/files/presigned-upload/', views.get_presigned_upload, name='presigned_upload'),
    path('files/confirm-upload/', views.confirm_upload, name='confirm_upload'),
    
    # OPTIMIZACIÓN ULTRA: APIs para uploads masivos
    path('api/upload-progress/<str:upload_id>/', api.upload_progress, name='upload_progress'),
    path('api/upload-progress/<str:upload_id>/update/', api.update_upload_progress, name='update_upload_progress'),
    path('api/r2-health/', api.r2_health_check, name='r2_health_check'),
    path('api/upload-stats/', api.upload_stats, name='upload_stats'),
    path('api/optimize-settings/', api.optimize_upload_settings, name='optimize_upload_settings'),
    path('api/file-limits/', api.get_file_limits, name='get_file_limits'),
    path('api/storage-availability/', api.get_storage_availability, name='storage_availability'),
]