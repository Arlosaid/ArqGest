from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
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

    files_list = request.FILES.getlist('files')
    total_files = len(files_list)
    total_size = sum(f.size or 0 for f in files_list)
    
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
        base_max_size = float(os.environ.get('MAX_FILE_SIZE_MB', '1200'))  # 1.2GB para archivos de arquitectura
        # Aplicar límites específicos para mobile (archivos de arquitectura pueden ser pesados)
        if is_mobile_upload or is_mobile_device:
            MAX_FILE_SIZE_MB = min(base_max_size, 200.0)  # Max 200MB en mobile para planos/renders
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
    
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,3DS,MAX,ZIP,RAR,7Z,TIFF,DOC,DOCX,XLS,XLSX,PPT,PPTX,TXT,MD').split(','))

    # Limitación a 1 archivo por vez (MVP simplificado)
    if total_files > 1:
        error_msg = "Solo se permite subir 1 archivo por vez para mantener la simplicidad"
        log_operation(
            'FILE_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_TOO_MANY_FILES,
            project_id=project_id,
            phase_id=phase_id,
            files_count=total_files,
            max_files_allowed=1
        )
        messages.error(request, error_msg)
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({"error": error_msg, "success": False}, status=413)
        return HttpResponse(status=413)

    # PRIMERA FASE: Validar TODOS los archivos antes de procesar ninguno
    # Verificar límite de almacenamiento de la organización
    from apps.orgs.storage_service import StorageService
    organization = phase.project.organization
    
    # Calcular el tamaño total de todos los archivos a subir
    total_upload_size = sum(f.size or 0 for f in files_list)
    
    # Verificar si se puede subir
    can_upload, storage_error, storage_data = StorageService.can_upload_file(
        organization, total_upload_size
    )
    
    if not can_upload:
        log_operation(
            'FILE_UPLOAD_ERROR',
            request.user.email,
            logger,
            level='WARNING',
            error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_LIMIT,
            project_id=project_id,
            phase_id=phase_id,
            upload_size_mb=round(total_upload_size / (1024 * 1024), 2),
            storage_used_gb=storage_data['total_gb'],
            storage_limit_gb=storage_data['plan_limit_gb'],
            remaining_gb=storage_data['remaining_gb']
        )
        return JsonResponse({
            "success": False, 
            "error": storage_error,
            "error_type": "storage_limit"
        }, status=413)  # 413 Payload Too Large
    
    validation_errors = []
    valid_files = []
    
    for uploaded_file in files_list:
        size_mb = (uploaded_file.size or 0) / (1024 * 1024)
        ext = os.path.splitext(uploaded_file.name)[1].replace('.', '').upper()
        file_errors = []
        
        # OPTIMIZACIÓN: Usar validador robusto
        try:
            from .validators import validate_project_file
            validate_project_file(uploaded_file)
        except ValidationError as e:
            file_errors.extend(e.messages)
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
                validation_errors=e.messages[:3]  # Primeros 3 errores
            )
            continue  # Saltar al siguiente archivo
        
        # Validar extensión (fallback si no se usó el validador completo)
        if ext not in ALLOWED_EXTENSIONS:
            file_errors.append(f"Tipo de archivo no permitido (.{ext.lower()})")
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
                allowed_extensions=list(ALLOWED_EXTENSIONS)[:10]
            )
        
        # Validación básica de contenido (solo verificar que el archivo no esté vacío y tenga contenido válido)
        try:
            if uploaded_file.size == 0:
                file_errors.append(f"Archivo vacío")
                log_operation(
                    'FILE_UPLOAD_ERROR',
                    request.user.email,
                    logger,
                    level='WARNING',
                    error_code=FileErrorCodes.FILE_UPLOAD_EMPTY_FILE,
                    project_id=project_id,
                    phase_id=phase_id,
                    filename=uploaded_file.name,
                    size_bytes=0
                )
            elif uploaded_file.size < 10:  # Archivos sospechosamente pequeños
                file_errors.append(f"Archivo muy pequeño (posiblemente corrupto)")
                log_operation(
                    'FILE_UPLOAD_ERROR',
                    request.user.email,
                    logger,
                    level='WARNING',
                    error_code=FileErrorCodes.FILE_UPLOAD_SUSPICIOUS_FILE,
                    project_id=project_id,
                    phase_id=phase_id,
                    filename=uploaded_file.name,
                    size_bytes=uploaded_file.size,
                    reason='file_too_small'
                )
            
            # Verificación básica de nombre de archivo
            if len(uploaded_file.name) > 255:
                file_errors.append(f"Nombre de archivo muy largo (máx: 255 caracteres)")
                log_operation(
                    'FILE_UPLOAD_ERROR',
                    request.user.email,
                    logger,
                    level='WARNING',
                    error_code=FileErrorCodes.FILE_UPLOAD_INVALID_FILENAME,
                    project_id=project_id,
                    phase_id=phase_id,
                    filename=uploaded_file.name,
                    filename_length=len(uploaded_file.name),
                    reason='filename_too_long'
                )
            
            # Verificar caracteres peligrosos en nombre
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
            if any(char in uploaded_file.name for char in dangerous_chars):
                file_errors.append(f"Nombre de archivo contiene caracteres no permitidos")
                found_chars = [char for char in dangerous_chars if char in uploaded_file.name]
                log_operation(
                    'FILE_UPLOAD_ERROR',
                    request.user.email,
                    logger,
                    level='WARNING',
                    error_code=FileErrorCodes.FILE_UPLOAD_INVALID_FILENAME,
                    project_id=project_id,
                    phase_id=phase_id,
                    filename=uploaded_file.name,
                    dangerous_chars=found_chars,
                    reason='dangerous_characters'
                )
                
        except Exception as e:
            log_operation(
                'FILE_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_UPLOAD_METADATA_ERROR,
                project_id=project_id,
                phase_id=phase_id,
                filename=uploaded_file.name,
                error_message=str(e)
            )
        
        # Validar tamaño
        if size_mb > MAX_FILE_SIZE_MB:
            file_errors.append(f"Muy grande ({size_mb:.1f}MB, máx: {MAX_FILE_SIZE_MB}MB)")
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
        
        if file_errors:
            validation_errors.append(f"{uploaded_file.name}: {', '.join(file_errors)}")
        else:
            valid_files.append(uploaded_file)
    
    # Si hay errores de validación, devolver todos juntos
    if validation_errors:
        error_msg = f"Archivos no válidos encontrados:\n• " + "\n• ".join(validation_errors)
        
        messages.error(request, error_msg)
        if request.headers.get('HX-Request') == 'true':
            return JsonResponse({
                "error": error_msg,
                "success": False,
                "validation_errors": validation_errors,
                "valid_files_count": len(valid_files),
                "invalid_files_count": len(validation_errors)
            }, status=400)
        return HttpResponse(status=400)
    
    # SEGUNDA FASE: Procesar solo archivos válidos
    successful_uploads = 0
    failed_uploads = 0
    failed_reasons = []

    for uploaded_file in valid_files:

        try:
            # 🔥 CRÍTICO: Asegurar que el puntero del archivo esté al inicio antes de guardar
            try:
                uploaded_file.seek(0)
            except Exception:
                pass  # No crítico si falla
            
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
                    # OPTIMIZACIÓN: Resetear puntero del archivo antes del checksum
                    uploaded_file.seek(0)
                    hasher = hashlib.sha256()
                    for chunk in uploaded_file.chunks():
                        hasher.update(chunk)
                    instance.checksum_sha256 = hasher.hexdigest()
                    instance.save(update_fields=["checksum_sha256"])
                    
                    # Detectar archivos duplicados por checksum
                    if instance.checksum_sha256:
                        duplicate = ProjectFile.objects.filter(
                            phase=phase,
                            checksum_sha256=instance.checksum_sha256
                        ).exclude(pk=instance.pk).first()
                        
                        if duplicate:
                            log_operation(
                                'FILE_UPLOAD_DUPLICATE_DETECTED',
                                request.user.email,
                                logger,
                                level='WARNING',
                                error_code=FileErrorCodes.FILE_UPLOAD_DUPLICATE_CHECKSUM,
                                file_id=instance.id,
                                duplicate_file_id=duplicate.id,
                                checksum=instance.checksum_sha256,
                                filename=uploaded_file.name,
                                duplicate_filename=duplicate.filename
                            )
                            
                            # Eliminar el archivo duplicado recién subido
                            instance.file.delete(save=False)
                            instance.delete()
                            
                            # Notificar al usuario sobre el duplicado
                            duplicate_msg = f"Este archivo ya existe como '{duplicate.filename}' (subido el {duplicate.uploaded_at.strftime('%d/%m/%Y')})"
                            
                            if request.headers.get('HX-Request') == 'true':
                                html_response = f'''
                                <script>
                                    if (window.notifications) {{
                                        window.notifications.warning('{duplicate_msg}');
                                    }} else if (window.showGlobalNotification) {{
                                        window.showGlobalNotification('{duplicate_msg}', 'warning');
                                    }}
                                    
                                    // Trigger para recargar la lista
                                    setTimeout(() => {{
                                        const container = document.getElementById('files-container-{phase.id}');
                                        if (container && window.htmx) {{
                                            htmx.trigger(container, 'fileUploaded');
                                        }}
                                    }}, 100);
                                </script>
                                '''
                                return HttpResponse(html_response)
                            else:
                                return JsonResponse({
                                    "success": False,
                                    "duplicate": True,
                                    "existing_file_id": duplicate.id,
                                    "message": duplicate_msg
                                }, status=200)  # 200 porque técnicamente no es un error
                    
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

    # Guardar información mínima para logging
    file_info = {
        'filename': project_file.filename,
        'size_bytes': project_file.size_bytes,
        'extension': project_file.extension,
        'project_id': project_file.phase.project.id,
        'phase_id': project_file.phase.id
    }

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
    
    # HTMX: devolver script para recargar la lista y mostrar notificación
    if request.headers.get('HX-Request') == 'true':
        html_response = f'''
        <script>
            // Mostrar notificación de éxito
            if (window.notifications) {{
                window.notifications.success('Archivo eliminado exitosamente');
            }} else if (window.showGlobalNotification) {{
                window.showGlobalNotification('Archivo eliminado exitosamente', 'success');
            }}
            
            // Trigger para recargar archivos
            setTimeout(() => {{
                document.body.dispatchEvent(new CustomEvent('fileUploaded'));
                
                // También recargar contenedor específico si existe
                const container = document.getElementById('files-container-{file_info["phase_id"]}');
                if (container && window.htmx) {{
                    htmx.trigger(container, 'fileUploaded');
                }}
            }}, 100);
        </script>
        '''
        return HttpResponse(html_response)

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
    file_size = int(request.POST.get('file_size', 0)) or (request.body and int(json.loads(request.body).get('file_size', 0)))
    
    # Verificar límite de almacenamiento antes de generar URL presignada
    if file_size > 0:
        from apps.orgs.storage_service import StorageService
        organization = phase.project.organization
        
        can_upload, storage_error, storage_data = StorageService.can_upload_file(
            organization, file_size
        )
        
        if not can_upload:
            log_operation(
                'PRESIGNED_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_LIMIT,
                project_id=project_id,
                phase_id=phase_id,
                filename=filename,
                file_size_mb=round(file_size / (1024 * 1024), 2),
                storage_used_gb=storage_data['total_gb'],
                storage_limit_gb=storage_data['plan_limit_gb'],
                remaining_gb=storage_data['remaining_gb']
            )
            return JsonResponse({
                "error": storage_error,
                "error_type": "storage_limit"
            }, status=413)
    
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

        # OPTIMIZACIÓN: Usar cliente R2 optimizado para archivos grandes
        try:
            from core.r2_config import get_optimized_r2_client
            s3 = get_optimized_r2_client()
        except ImportError:
            # Fallback al cliente básico
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

        # CRÍTICO: Tiempo de expiración extendido para archivos grandes
        expires_seconds = int(os.environ.get('PRESIGN_EXPIRES_SECONDS', '7200'))  # 2 horas por defecto
        
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params=params,
            ExpiresIn=expires_seconds,
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
    
    # Verificar límite de almacenamiento antes de confirmar
    if size_bytes > 0:
        from apps.orgs.storage_service import StorageService
        organization = phase.project.organization
        
        can_upload, storage_error, storage_data = StorageService.can_upload_file(
            organization, size_bytes
        )
        
        if not can_upload:
            log_operation(
                'CONFIRM_UPLOAD_ERROR',
                request.user.email,
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_LIMIT,
                project_id=project_id,
                phase_id=phase_id,
                key=key,
                file_size_mb=round(size_bytes / (1024 * 1024), 2),
                storage_used_gb=storage_data['total_gb'],
                storage_limit_gb=storage_data['plan_limit_gb'],
                remaining_gb=storage_data['remaining_gb']
            )
            return JsonResponse({
                "error": storage_error,
                "error_type": "storage_limit"
            }, status=413)
    
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
        instance = ProjectFile(
            phase=phase, 
            uploaded_by=request.user, 
            size_bytes=size_bytes, 
            content_type=content_type
        )
        
        # 🔥 CRÍTICO: Asignar el key directamente al FileField (django-storages S3)
        # Para R2/S3, el archivo ya fue subido directamente, solo asignamos la referencia
        instance.file.name = key
        
        # Derivar ext_upper del key
        try:
            instance.ext_upper = os.path.splitext(key)[1].replace('.', '').upper()
        except Exception as e:
            logger.warning(f"Could not derive extension from key {key}: {e}")
            instance.ext_upper = ''
        
        # 🔥 CRÍTICO: Guardar sin intentar volver a subir el archivo
        # Como el archivo ya está en R2, solo guardamos el registro en la DB
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
        
        # 🔥 FIX: Invalidar caché de archivos para que aparezcan inmediatamente
        from .cache_utils import invalidate_phase_files_cache
        invalidate_phase_files_cache(phase_id)
        
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
