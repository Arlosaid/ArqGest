from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import ProjectFile, project_file_path
from apps.projects.models import Phase
import os
import hashlib
import json

try:
    import boto3
except Exception:
    boto3 = None

@login_required
@require_POST
def upload_file(request, project_id, phase_id):
    """Handles file upload and returns an updated file list for HTMX."""
    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    
    if request.user.organization != phase.project.organization:
        return HttpResponseForbidden(_("You do not have permission to access this resource."))

    if not request.FILES.getlist('files'):
        # This case might not be hit if the input is 'required', but it's good practice.
        messages.error(request, "No se seleccionaron archivos.")
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({"error": "No se seleccionaron archivos."}, status=400)
        return HttpResponse(status=400)

    # Validaciones básicas en servidor (mientras no haya upload directo a R2)
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '600'))
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF,DOC,DOCX,XLS,XLSX,PPT,PPTX,TXT,MD').split(','))

    for uploaded_file in request.FILES.getlist('files'):
        size_mb = (uploaded_file.size or 0) / (1024 * 1024)
        ext = os.path.splitext(uploaded_file.name)[1].replace('.', '').upper()
        if ext not in ALLOWED_EXTENSIONS:
            error_msg = f"Tipo de archivo no permitido: {ext}"
            messages.error(request, error_msg)
            if request.headers.get('HX-Request') == 'true':
                return JsonResponse({"error": error_msg}, status=400)
            return HttpResponse(status=400)
        if size_mb > MAX_FILE_SIZE_MB:
            error_msg = f"El archivo excede el límite de tamaño ({MAX_FILE_SIZE_MB} MB)"
            messages.error(request, error_msg)
            if request.headers.get('HX-Request') == 'true':
                return JsonResponse({"error": error_msg}, status=413)
            return HttpResponse(status=413)

        instance = ProjectFile.objects.create(
            phase=phase,
            file=uploaded_file,
            uploaded_by=request.user
        )
        # Opcional: calcular checksum sha256 (limitado por tamaño para evitar costo excesivo)
        try:
            max_checksum_mb = int(os.environ.get('MAX_CHECKSUM_MB', '50'))
            if (uploaded_file.size or 0) <= max_checksum_mb * 1024 * 1024:
                hasher = hashlib.sha256()
                for chunk in uploaded_file.chunks():
                    hasher.update(chunk)
                instance.checksum_sha256 = hasher.hexdigest()
                instance.save(update_fields=["checksum_sha256"])
        except Exception:
            pass
    
    messages.success(request, "Archivo(s) subido(s) exitosamente.")

    # Si es una petición HTMX, devolvemos solo la lista actualizada
    if request.headers.get('HX-Request') == 'true':
        # Determinar qué template usar basado en el target
        hx_target = request.headers.get('HX-Target', '')
        if 'files-table' in hx_target:
            # Si el target es una tabla, devolver el template de tabla simplificado
            from apps.projects.models import Project
            
            project = phase.project
            
            # Contexto simplificado sin paginación
            context = {
                'phase': phase,
                'project': project,
            }
            return render(request, 'projects/partials/files_table.html', context)
        else:
            # Target por defecto: lista de archivos
            files = phase.files.all()
            return render(request, 'projects/partials/file_list.html', {'files': files})

    # En formularios normales, redirigir al detalle del proyecto (pestaña Archivos)
    project_url = reverse('projects:project-detail', kwargs={'pk': phase.project_id})
    return redirect(f"{project_url}?tab=files#files")

@login_required
@require_POST
def delete_file(request, file_id):
    """Handles the deletion of a project file.

    - Si es HTMX, responde vacío (204) para que el frontend remueva el elemento.
    - Si es una llamada normal/fetch, responde JSON con success.
    """
    project_file = get_object_or_404(ProjectFile, id=file_id)
    
    if request.user.organization != project_file.phase.project.organization:
        return HttpResponseForbidden("No tienes permiso para acceder a este recurso.")

    project_file.file.delete(save=False)
    project_file.delete()
    
    # HTMX: devolver 200 con cuerpo vacío para que outerHTML se reemplace por nada
    if request.headers.get('HX-Request') == 'true':
        return HttpResponse("")

    # Fetch/normal: JSON
    return JsonResponse({"success": True, "id": file_id})


@login_required
@require_POST
def get_presigned_upload(request, project_id, phase_id):
    """Devuelve una URL firmada para subir directo a R2/S3.

    Requiere ENABLE_STORAGES=true y variables AWS/R2 configuradas.
    """
    if os.environ.get('ENABLE_STORAGES', 'false').lower() != 'true':
        return JsonResponse({"error": "almacenamiento no habilitado"}, status=400)
    if boto3 is None:
        return JsonResponse({"error": "boto3 no disponible"}, status=500)

    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    if request.user.organization != phase.project.organization:
        return HttpResponseForbidden("No tienes permiso para acceder a este recurso.")

    filename = request.POST.get('filename') or (request.body and (json.loads(request.body).get('filename')))
    content_type = request.POST.get('content_type') or (request.body and (json.loads(request.body).get('content_type')))
    if not filename:
        return JsonResponse({"error": "nombre de archivo requerido"}, status=400)

    # Construir key de almacenamiento
    dummy = ProjectFile(phase=phase)
    key = project_file_path(dummy, filename)

    session = boto3.session.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'auto'),
    )
    s3 = session.client('s3', endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None))
    params = {
        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
        'Key': key,
    }
    if content_type:
        params['ContentType'] = content_type

    url = s3.generate_presigned_url(
        ClientMethod='put_object',
        Params=params,
        ExpiresIn=int(os.environ.get('PRESIGN_EXPIRES_SECONDS', '3600')),
    )
    return JsonResponse({'url': url, 'key': key})


@login_required
@require_POST
def confirm_upload(request):
    """Confirma una subida directa y crea el registro ProjectFile.

    Espera: key, project_id, phase_id, size_bytes, content_type (opcional).
    Requiere storages habilitado.
    """
    if os.environ.get('ENABLE_STORAGES', 'false').lower() != 'true':
        return JsonResponse({"error": "almacenamiento no habilitado"}, status=400)

    data = request.POST.dict()
    if not data and request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

    key = data.get('key')
    project_id = data.get('project_id')
    phase_id = data.get('phase_id')
    size_bytes = int(data.get('size_bytes') or 0)
    content_type = data.get('content_type') or ''
    if not (key and project_id and phase_id):
        return JsonResponse({"error": "clave, project_id, phase_id requeridos"}, status=400)

    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    if request.user.organization != phase.project.organization:
        return HttpResponseForbidden("No tienes permiso para acceder a este recurso.")

    instance = ProjectFile(phase=phase, uploaded_by=request.user, size_bytes=size_bytes, content_type=content_type)
    # Asignar el key directamente al FileField (django-storages S3)
    instance.file.name = key
    # Derivar ext_upper
    try:
        instance.ext_upper = os.path.splitext(key)[1].replace('.', '').upper()
    except Exception:
        pass
    instance.save()
    return JsonResponse({"success": True, "id": instance.id})
