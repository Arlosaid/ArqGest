from django.urls import path
from . import views

app_name = 'files'

urlpatterns = [
    # Ejemplo: /projects/1/phases/2/files/upload/
    path('projects/<int:project_id>/phases/<int:phase_id>/files/upload/', views.upload_file, name='upload_file'),
    # Ejemplo: /files/3/delete/
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    # Presigned URL endpoints (opcional para R2/S3)
    path('projects/<int:project_id>/phases/<int:phase_id>/files/presign-upload/', views.get_presigned_upload, name='presign_upload'),
    path('files/confirm-upload/', views.confirm_upload, name='confirm_upload'),
]
