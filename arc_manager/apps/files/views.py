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
from core.error_codes import log_operation, FileErrorCodes
import os
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

try:
    import boto3
except Exception:
    boto3 = None

@login_required
@require_POST
def upload_file(request, project_id, phase_id):
    """
    Handles file upload optimized for large files with minimal server impact.
    
    Optimizations:
    - Streams large files directly to disk
    - Limits memory usage to 25MB max per request
    - Mobile-specific optimizations for sequential uploads
    - Provides detailed logging for performance monitoring
    """
    # Detectar si es un upload desde mobile
    is_mobile_upload = request.headers.get('X-Mobile-Upload') == 'true'
    user_agent = request.headers.get('User-Agent', '')
    is_mobile_device = any(keyword in user_agent.lower() for keyword in 
                          ['android', 'iphone', 'ipad', 'mobile', 'tablet'])
    # Log inicial de intento de upload (con info de mobile)
    log_operation(
        'FILE_UPLOAD_ATTEMPT',
        request.user.email,
        logger,
        level='INFO',
        project_id=project_id,
        phase_id=phase_id,
        user_id=request.user.id,
        organization_id=request.user.organization.id if request.user.organization else None,
        ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'unknown')[:100],
        is_mobile_upload=is_mobile_upload,
        is_mobile_device=is_mobile_device
    )
    
    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    
    if request.user.organization != phase.project.organization:
        log_operation(
            'FILE_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_PERMISSION_DENIED,
            project_id=project_id,
            phase_id=phase_id
        )
        return HttpResponseForbidden(_("You do not have permission to access this resource."))

    # Log detalles de archivos recibidos
    files_list = request.FILES.getlist('files')
    total_files = len(files_list)
    total_size = sum(f.size or 0 for f in files_list)
    
    log_operation(
        'FILE_UPLOAD_FILES_RECEIVED',
        request.user.email,
        logger,
        level='INFO',
        project_id=project_id,
        phase_id=phase_id,
        files_count=total_files,
        total_size_bytes=total_size,
        file_names=[f.name for f in files_list[:5]]  # Máximo 5 nombres para el log
    )
    
    if not files_list:
        # This case might not be hit if the input is 'required', but it's good practice.
        log_operation(
            'FILE_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_UNEXPECTED_ERROR,
            project_id=project_id,
            phase_id=phase_id,
            reason='no_files_selected'
        )
        error_msg = "No se seleccionaron archivos."
        messages.error(request, error_msg)
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({"error": error_msg, "success": False}, status=400)
        return HttpResponse(status=400)

    # Validaciones básicas en servidor (con optimizaciones para mobile)
    try:
        base_max_size = float(os.environ.get('MAX_FILE_SIZE_MB', '600'))
        # Aplicar límites específicos para mobile
        if is_mobile_upload or is_mobile_device:
            MAX_FILE_SIZE_MB = min(base_max_size, 50.0)  # Max 50MB en mobile
            MAX_FILES_MOBILE = int(os.environ.get('MAX_FILES_MOBILE', '10'))  # Max 10 archivos en mobile
        else:
            MAX_FILE_SIZE_MB = base_max_size
            MAX_FILES_MOBILE = None
    except ValueError:
        error_msg = "Configuración de tamaño de archivo inválida. Contacta al administrador."
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({"error": error_msg, "success": False}, status=500)
        else:
            messages.error(request, error_msg)
            return HttpResponse(status=500)
    
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,ZIP,RAR,TIFF,DOC,DOCX,XLS,XLSX,PPT,PPTX,TXT,MD').split(','))

    # Validación específica para mobile: límite de archivos
    if (is_mobile_upload or is_mobile_device) and MAX_FILES_MOBILE and total_files > MAX_FILES_MOBILE:
        error_msg = f"Demasiados archivos para móvil. Máximo {MAX_FILES_MOBILE} archivos por vez"
        log_operation(
            'FILE_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_TOO_MANY_FILES,
            project_id=project_id,
            phase_id=phase_id,
            files_count=total_files,
            max_files_mobile=MAX_FILES_MOBILE,
            is_mobile=is_mobile_upload or is_mobile_device
        )
        messages.error(request, error_msg)
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({"error": error_msg, "success": False}, status=413)
        return HttpResponse(status=413)

    # Contadores para resumen final
    successful_uploads = 0
    failed_uploads = 0
    failed_reasons = []

    for uploaded_file in files_list:
        size_mb = (uploaded_file.size or 0) / (1024 * 1024)
        ext = os.path.splitext(uploaded_file.name)[1].replace('.', '').upper()
        if ext not in ALLOWED_EXTENSIONS:
            error_msg = f"Tipo de archivo no permitido: {ext}"
            failed_uploads += 1
            failed_reasons.append(f"{uploaded_file.name}: tipo no permitido ({ext})")
            log_operation(
                'FILE_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_UPLOAD_INVALID_TYPE,
                project_id=project_id,
                phase_id=phase_id,
                filename=uploaded_file.name,
                extension=ext,
                allowed_extensions=list(ALLOWED_EXTENSIONS)[:10]  # Primeras 10 para el log
            )
            messages.error(request, error_msg)
            if request.headers.get('HX-Request') == 'true':
                return JsonResponse({"error": error_msg, "success": False}, status=400)
            return HttpResponse(status=400)
        if size_mb > MAX_FILE_SIZE_MB:
            error_msg = f"El archivo excede el límite de tamaño ({MAX_FILE_SIZE_MB} MB)"
            failed_uploads += 1
            failed_reasons.append(f"{uploaded_file.name}: muy grande ({size_mb:.1f}MB)")
            log_operation(
                'FILE_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_UPLOAD_TOO_LARGE,
                project_id=project_id,
                phase_id=phase_id,
                filename=uploaded_file.name,
                size_mb=round(size_mb, 2),
                size_bytes=uploaded_file.size,
                max_size_mb=MAX_FILE_SIZE_MB
            )
            messages.error(request, error_msg)
            if request.headers.get('HX-Request') == 'true':
                return JsonResponse({"error": error_msg, "success": False}, status=413)
            return HttpResponse(status=413)

        try:
            instance = ProjectFile.objects.create(
                phase=phase,
                file=uploaded_file,
                uploaded_by=request.user
            )
            
            successful_uploads += 1
            
            # Log exitoso de creación de archivo con más detalles
            log_operation(
                'FILE_UPLOAD_SUCCESS',
                request.user.email,
                logger,
                level='INFO',
                project_id=project_id,
                phase_id=phase_id,
                file_id=instance.id,
                filename=uploaded_file.name,
                size_bytes=uploaded_file.size or 0,
                size_mb=round(size_mb, 2),
                extension=ext,
                file_path=instance.file.name if instance.file else None,
                organization_id=request.user.organization.id if request.user.organization else None
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
                    
                    # Log de checksum calculado
                    log_operation(
                        'FILE_CHECKSUM_CALCULATED',
                        request.user.email,
                        logger,
                        level='DEBUG',
                        file_id=instance.id,
                        checksum=instance.checksum_sha256
                    )
            except Exception as e:
                # Log de error en cálculo de checksum
                log_operation(
                    'FILE_CHECKSUM_ERROR',
                    request.user.email,
                    logger,
                    level='WARNING',
                    error_code=FileErrorCodes.FILE_PROCESSING_METADATA_EXTRACTION_ERROR,
                    file_id=instance.id,
                    error_message=str(e)
                )
                
        except Exception as e:
            failed_uploads += 1
            failed_reasons.append(f"{uploaded_file.name}: error de storage")
            
            # Log de error en creación de archivo con stack trace
            import traceback
            log_operation(
                'FILE_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='ERROR',
                error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
                project_id=project_id,
                phase_id=phase_id,
                filename=uploaded_file.name,
                size_bytes=uploaded_file.size or 0,
                extension=ext,
                error_message=str(e),
                stack_trace=traceback.format_exc()[:500]  # Limitamos el stack trace
            )
            error_msg = "Error al guardar el archivo."
            messages.error(request, error_msg)
            if request.headers.get('HX-Request') == 'true':
                return JsonResponse({"error": error_msg, "success": False}, status=500)
            return HttpResponse(status=500)
    
    # Log de resumen final del upload batch
    log_operation(
        'FILE_UPLOAD_BATCH_COMPLETED',
        request.user.email,
        logger,
        level='INFO',
        project_id=project_id,
        phase_id=phase_id,
        total_files=total_files,
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        total_size_bytes=total_size,
        failed_reasons=failed_reasons[:3] if failed_reasons else [],  # Máximo 3 razones de fallo
        duration_ms=None  # Podríamos calcular tiempo si fuera necesario
    )
    
    # Invalidar caché de archivos para esta fase
    if successful_uploads > 0:
        from .cache_utils import invalidate_phase_files_cache
        invalidate_phase_files_cache(phase_id)

    # Para HTMX, no usar Django messages, usar notificaciones JavaScript
    # messages.success(request, "Archivo(s) subido(s) exitosamente.")

    # Si es una petición HTMX, devolvemos solo la lista actualizada
    if request.headers.get('HX-Request') == 'true':
        # OPTIMIZACIÓN para Railway: En lugar de llamar a la vista completa paginada
        # que puede causar timeout, devolvemos directamente un trigger para recargar
        # Esto evita el procesamiento pesado después del upload
        
        hx_target = request.headers.get('HX-Target', '')
        if 'files-container' in hx_target:
            # Respuesta optimizada que dispara un evento para recargar los archivos
            # En lugar de renderizar todo inmediatamente (que causa timeout en Railway)
            html_response = '''
            <script>
                // Mostrar notificación de éxito usando el sistema personalizado
                if (window.notifications) {
                    window.notifications.success('¡Archivo subido exitosamente!');
                } else if (window.showGlobalNotification) {
                    window.showGlobalNotification('¡Archivo subido exitosamente!', 'success');
                }
                
                // Trigger inmediato para recargar los archivos después del upload exitoso
                setTimeout(() => {
                    const container = document.getElementById('files-container-' + ''' + str(phase.id) + ''');
                    if (container) {
                        // Disparar recarga sin bloquear la respuesta del upload
                        htmx.trigger(container, 'fileUploaded');
                    }
                }, 100);
            </script>
            '''
            return HttpResponse(html_response)
        elif 'files-table' in hx_target:
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
            # Target por defecto: usar notificaciones personalizadas + trigger de recarga
            # No devolver contenido HTML para el target, solo script para notificar y recargar
            html_response = '''
            <script>
                // Mostrar notificación de éxito usando el sistema personalizado
                if (window.notifications) {
                    window.notifications.success('¡Archivo subido exitosamente!');
                } else if (window.showGlobalNotification) {
                    window.showGlobalNotification('¡Archivo subido exitosamente!', 'success');
                }
                
                // Trigger para recargar la lista completa
                setTimeout(() => {
                    document.body.dispatchEvent(new CustomEvent('fileUploaded'));
                }, 100);
            </script>
            '''
            return HttpResponse(html_response)

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
    # Log inicial de intento de eliminación
    log_operation(
        'FILE_DELETE_ATTEMPT',
        request.user.email,
        logger,
        level='INFO',
        file_id=file_id,
        user_id=request.user.id,
        organization_id=request.user.organization.id if request.user.organization else None,
        ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'unknown')[:100]
    )
    
    project_file = get_object_or_404(ProjectFile, id=file_id)
    
    if request.user.organization != project_file.phase.project.organization:
        # Log intento de eliminación sin permisos
        log_operation(
            'FILE_DELETE_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_DOWNLOAD_PERMISSION_DENIED,
            file_id=file_id,
            project_id=project_file.phase.project.id,
            phase_id=project_file.phase.id
        )
        return HttpResponseForbidden("No tienes permiso para acceder a este recurso.")

    # Guardar información del archivo para el log antes de eliminarlo
    file_info = {
        'filename': project_file.filename,
        'size_bytes': project_file.size_bytes,
        'extension': project_file.extension,
        'project_id': project_file.phase.project.id,
        'phase_id': project_file.phase.id,
        'checksum': project_file.checksum_sha256,
        'uploaded_at': project_file.uploaded_at.isoformat() if project_file.uploaded_at else None,
        'uploaded_by_id': project_file.uploaded_by.id if project_file.uploaded_by else None,
        'uploaded_by_email': project_file.uploaded_by.email if project_file.uploaded_by else None,
        'file_path': project_file.file.name if project_file.file else None,
        'project_name': project_file.phase.project.name if project_file.phase and project_file.phase.project else None,
        'phase_name': project_file.phase.name if project_file.phase else None
    }
    
    # Log detalles del archivo antes de eliminación
    log_operation(
        'FILE_DELETE_DETAILS',
        request.user.email,
        logger,
        level='INFO',
        file_id=file_id,
        **file_info
    )

    try:
        # Eliminar archivo físico del almacenamiento
        project_file.file.delete(save=False)
        # Eliminar registro de base de datos
        project_file.delete()
        
        # Log exitoso de eliminación
        log_operation(
            'FILE_DELETE_SUCCESS',
            request.user.email,
            logger,
            level='INFO',
            file_id=file_id,
            filename=file_info['filename'],
            size_bytes=file_info['size_bytes'],
            extension=file_info['extension'],
            project_id=file_info['project_id'],
            phase_id=file_info['phase_id']
        )
        
        # Invalidar caché de archivos para esta fase
        from .cache_utils import invalidate_phase_files_cache
        invalidate_phase_files_cache(file_info['phase_id'])
        
    except Exception as e:
        # Log error en eliminación con stack trace completo
        import traceback
        log_operation(
            'FILE_DELETE_ERROR',
            request.user.email,
            logger,
            level='ERROR',
            error_code=FileErrorCodes.FILE_MANAGEMENT_DELETE_ERROR,
            file_id=file_id,
            filename=file_info['filename'],
            project_id=file_info['project_id'],
            phase_id=file_info['phase_id'],
            size_bytes=file_info['size_bytes'],
            extension=file_info['extension'],
            error_message=str(e),
            stack_trace=traceback.format_exc()[:500],
            file_path=file_info['file_path'],
            project_name=file_info['project_name'],
            phase_name=file_info['phase_name']
        )
        
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({"error": "Error al eliminar el archivo."}, status=500)
        return JsonResponse({"success": False, "error": "Error al eliminar el archivo."}, status=500)
    
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
        log_operation(
            'PRESIGNED_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
            project_id=project_id,
            phase_id=phase_id,
            reason='storages_disabled'
        )
        return JsonResponse({"error": "almacenamiento externo no habilitado"}, status=400)
        
    if boto3 is None:
        log_operation(
            'PRESIGNED_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='ERROR',
            error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
            project_id=project_id,
            phase_id=phase_id,
            reason='boto3_unavailable'
        )
        return JsonResponse({"error": "boto3 no disponible"}, status=500)

    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    if not request.user.is_superuser and request.user.organization != phase.project.organization:
        log_operation(
            'PRESIGNED_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_PERMISSION_DENIED,
            project_id=project_id,
            phase_id=phase_id
        )
        return HttpResponseForbidden("No tienes permiso para acceder a este recurso.")

    filename = request.POST.get('filename') or (request.body and (json.loads(request.body).get('filename')))
    content_type = request.POST.get('content_type') or (request.body and (json.loads(request.body).get('content_type')))
    if not filename:
        log_operation(
            'PRESIGNED_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_INVALID_FILENAME,
            project_id=project_id,
            phase_id=phase_id
        )
        return JsonResponse({"error": "nombre de archivo requerido"}, status=400)

    try:
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
        
        # Log exitoso de generación de URL presignada
        log_operation(
            'PRESIGNED_UPLOAD_SUCCESS',
            request.user.email,
            logger,
            level='INFO',
            project_id=project_id,
            phase_id=phase_id,
            filename=filename,
            key=key,
            expires_seconds=int(os.environ.get('PRESIGN_EXPIRES_SECONDS', '3600'))
        )
        
        return JsonResponse({'url': url, 'key': key})
        
    except Exception as e:
        # Log error en generación de URL presignada
        log_operation(
            'PRESIGNED_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='ERROR',
            error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
            project_id=project_id,
            phase_id=phase_id,
            filename=filename,
            error_message=str(e)
        )
        return JsonResponse({"error": "Error generando URL de subida"}, status=500)


@login_required
@require_POST
def confirm_upload(request):
    """Confirma una subida directa y crea el registro ProjectFile.

    Espera: key, project_id, phase_id, size_bytes, content_type (opcional).
    Requiere storages habilitado.
    """
    if os.environ.get('ENABLE_STORAGES', 'false').lower() != 'true':
        log_operation(
            'CONFIRM_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
            reason='storages_disabled'
        )
        return JsonResponse({"error": "almacenamiento externo no habilitado"}, status=400)

    data = request.POST.dict()
    if not data and request.body:
        try:
            data = json.loads(request.body)
        except Exception as e:
            log_operation(
                'CONFIRM_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_UPLOAD_METADATA_ERROR,
                error_message=str(e)
            )
            data = {}

    key = data.get('key')
    project_id = data.get('project_id')
    phase_id = data.get('phase_id')
    size_bytes = int(data.get('size_bytes') or 0)
    content_type = data.get('content_type') or ''
    
    if not (key and project_id and phase_id):
        log_operation(
            'CONFIRM_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_METADATA_ERROR,
            key=key,
            project_id=project_id,
            phase_id=phase_id,
            reason='missing_required_parameters'
        )
        return JsonResponse({"error": "clave, project_id, phase_id requeridos"}, status=400)

    phase = get_object_or_404(Phase, id=phase_id, project_id=project_id)
    if not request.user.is_superuser and request.user.organization != phase.project.organization:
        log_operation(
            'CONFIRM_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_PERMISSION_DENIED,
            project_id=project_id,
            phase_id=phase_id,
            key=key
        )
        return HttpResponseForbidden("No tienes permiso para acceder a este recurso.")

    try:
        instance = ProjectFile(phase=phase, uploaded_by=request.user, size_bytes=size_bytes, content_type=content_type)
        # Asignar el key directamente al FileField (django-storages S3)
        instance.file.name = key
        # Derivar ext_upper
        try:
            instance.ext_upper = os.path.splitext(key)[1].replace('.', '').upper()
        except Exception:
            pass
        instance.save()
        
        # Log exitoso de confirmación de subida
        log_operation(
            'CONFIRM_UPLOAD_SUCCESS',
            request.user.email,
            logger,
            level='INFO',
            file_id=instance.id,
            project_id=project_id,
            phase_id=phase_id,
            key=key,
            size_bytes=size_bytes,
            content_type=content_type,
            extension=instance.ext_upper
        )
        
        return JsonResponse({"success": True, "id": instance.id})
        
    except Exception as e:
        # Log error en confirmación de subida
        log_operation(
            'CONFIRM_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='ERROR',
            error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
            project_id=project_id,
            phase_id=phase_id,
            key=key,
            size_bytes=size_bytes,
            error_message=str(e)
        )
        return JsonResponse({"error": "Error confirmando subida del archivo"}, status=500)
