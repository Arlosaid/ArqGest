
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.projects.models import Phase
import os
import logging

logger = logging.getLogger(__name__)

def project_file_path(instance, filename):
    """
    Generate the file path for a new project file.
    Example: organizations/org_1/projects/proj_3/phases/phase_5/document.pdf
    
    Security: Sanitizes filename to prevent path traversal attacks.
    """
    # Sanitize filename to prevent path traversal attacks
    # Remove dangerous characters and patterns
    sanitized_filename = filename
    
    # Remove null bytes
    sanitized_filename = sanitized_filename.replace('\x00', '')
    
    # Remove path traversal patterns (both Unix and Windows)
    sanitized_filename = sanitized_filename.replace('../', '')
    sanitized_filename = sanitized_filename.replace('..\\', '')
    
    # Remove absolute paths
    if sanitized_filename.startswith('/') or sanitized_filename.startswith('\\'):
        sanitized_filename = sanitized_filename.lstrip('/\\')
    
    # Get just the basename (no directory components)
    sanitized_filename = os.path.basename(sanitized_filename)
    
    # Truncate long filenames to prevent filesystem errors
    # Max filename length on most filesystems is 255 bytes
    if len(sanitized_filename) > 255:
        # Keep the extension
        name, ext = os.path.splitext(sanitized_filename)
        max_name_length = 255 - len(ext)
        sanitized_filename = name[:max_name_length] + ext
    
    return (f'organizations/{instance.phase.project.organization.id}/'
            f'projects/{instance.phase.project.id}/'
            f'phases/{instance.phase.id}/{sanitized_filename}')

class ProjectFile(models.Model):
    """Represents a file associated with a project's phase."""
    
    # Import the manager
    from .managers import ProjectFileManager
    
    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name=_("Phase")
    )
    file = models.FileField(
        _("File"),
        upload_to=project_file_path
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Uploaded By")
    )
    uploaded_at = models.DateTimeField(_("Upload Date"), auto_now_add=True)

    # Metadatos persistentes para consultas y métricas
    size_bytes = models.BigIntegerField(default=0, db_index=True)
    ext_upper = models.CharField(max_length=16, blank=True, db_index=True)
    content_type = models.CharField(max_length=128, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    
    # Manager optimizado
    objects = ProjectFileManager()

    class Meta:
        verbose_name = _("Project File")
        verbose_name_plural = _("Project Files")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['ext_upper', 'size_bytes']),
            # OPTIMIZACIÓN: Índice compuesto para consultas frecuentes
            models.Index(fields=['phase', 'uploaded_at']),
            models.Index(fields=['phase', 'ext_upper']),
            # OPTIMIZACIÓN: Índice para búsquedas por usuario
            models.Index(fields=['uploaded_by', 'uploaded_at']),
        ]

    def __str__(self):
        return self.file.name

    @property
    def size(self):
        """Returns the file size in a human-readable format."""
        if self.file and hasattr(self.file, 'size'):
            return self.file.size
        return 0

    @property
    def filename(self) -> str:
        """Nombre base del archivo sin la ruta."""
        try:
            return os.path.basename(self.file.name)
        except Exception:
            return self.file.name

    @property
    def extension(self) -> str:
        """Extensión del archivo, en mayúsculas, sin el punto (ej. PDF)."""
        if getattr(self, 'ext_upper', ''):
            return self.ext_upper
        try:
            _, ext = os.path.splitext(self.file.name)
            return ext.replace('.', '').upper()
        except Exception:
            return ""

    @property
    def file_extension(self) -> str:
        """Extensión del archivo en minúsculas para uso en CSS."""
        return self.extension.lower()

    @property
    def icon_class(self) -> str:
        """Retorna la clase CSS del icono según el tipo de archivo."""
        ext = self.extension.lower()
        
        # Documentos
        if ext in ['pdf']:
            return 'fa-file-pdf'
        elif ext in ['doc', 'docx']:
            return 'fa-file-word'
        elif ext in ['xls', 'xlsx']:
            return 'fa-file-excel'
        elif ext in ['ppt', 'pptx']:
            return 'fa-file-powerpoint'
        elif ext in ['txt', 'md']:
            return 'fa-file-alt'
        
        # Imágenes
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
            return 'fa-file-image'
        
        # Archivos CAD/Diseño
        elif ext in ['dwg', 'dxf', 'rvt', 'skp', '3ds', 'max']:
            return 'fa-drafting-compass'
        
        # Archivos comprimidos
        elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
            return 'fa-file-archive'
        
        # Archivos de video
        elif ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']:
            return 'fa-file-video'
        
        # Archivos de audio
        elif ext in ['mp3', 'wav', 'flac', 'aac', 'ogg']:
            return 'fa-file-audio'
        
        # Archivos de código
        elif ext in ['py', 'js', 'html', 'css', 'php', 'java', 'cpp', 'c', 'cs']:
            return 'fa-file-code'
        
        # Por defecto
        else:
            return 'fa-file'

    def clean(self):
        """
        Validaciones de seguridad del modelo.
        
        SECURITY CRITICAL: Previene que usuarios suban archivos a proyectos
        de organizaciones diferentes.
        """
        from django.core.exceptions import ValidationError
        
        # Validar que el usuario pertenece a la organización del proyecto
        if self.uploaded_by and self.phase:
            project_org = self.phase.project.organization
            user_org = self.uploaded_by.organization
            
            if user_org != project_org:
                raise ValidationError({
                    'uploaded_by': _(
                        'Usuario no puede subir archivos a proyectos de otra organización. '
                        f'Usuario pertenece a {user_org}, proyecto pertenece a {project_org}.'
                    )
                })

    def save(self, *args, **kwargs):
        from core.error_codes import FileErrorCodes
        # FIXME: Migrar a structured_logging después del deploy
        # from core.structured_logging import log_error
        
        # FIXME: Función temporal hasta migrar a structured_logging
        def log_operation(*args, **kwargs):
            """Temporal stub para evitar errores durante deploy"""
            pass
        
        # SECURITY: Ejecutar validaciones antes de guardar
        self.clean()
        
        is_new = self.pk is None
        
        # 🔥 CRÍTICO: Si es un archivo nuevo, asegurar que el puntero esté al inicio
        if is_new and self.file:
            try:
                # Resetear puntero antes de guardar
                if hasattr(self.file, 'seek'):
                    self.file.seek(0)
                    logger.debug(f"File pointer reset: {self.file.name}")
                
                # Verificar que el archivo tenga contenido
                if hasattr(self.file, 'size') and (self.file.size or 0) > 0:
                    logger.debug(f"File with content: {self.file.size} bytes")
                else:
                    logger.warning(f"File without defined size: {self.file.name}")
                    
            except Exception as e:
                logger.warning(f"Could not reset file pointer: {e}")
        
        # Completar metadatos si están disponibles
        try:
            # Solo actualizar size_bytes si es un archivo nuevo Y no tiene un valor establecido
            # Para archivos nuevos con size_bytes=0, actualizar al tamaño real
            # Para archivos que especifican size_bytes > 0, respetar ese valor (tests)
            if self.file and hasattr(self.file, 'size') and is_new:
                file_size = int(getattr(self.file, 'size', 0) or 0)
                # Solo actualizar si size_bytes es 0 (no establecido manualmente)
                if self.size_bytes == 0:
                    self.size_bytes = file_size
        except Exception as e:
            # Log error en procesamiento de metadatos
            log_operation(
                'FILE_METADATA_ERROR',
                getattr(self.uploaded_by, 'email', 'system'),
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_PROCESSING_METADATA_EXTRACTION_ERROR,
                file_id=self.pk,
                error_message=str(e)
            )
            
        try:
            name = (self.file.name if self.file else '')
            # Solo actualizar ext_upper si no está establecido
            # Esto permite que los tests establezcan un valor específico
            if not self.ext_upper:
                self.ext_upper = os.path.splitext(name)[1].replace('.', '').upper() if name else ''
        except Exception as e:
            # Log error en procesamiento de extensión
            log_operation(
                'FILE_EXTENSION_ERROR',
                getattr(self.uploaded_by, 'email', 'system'),
                logger,
                level='WARNING',
                error_code=FileErrorCodes.FILE_PROCESSING_METADATA_EXTRACTION_ERROR,
                file_id=self.pk,
                filename=name,
                error_message=str(e)
            )
            
        try:
            super().save(*args, **kwargs)
            
            # Log exitoso de creación o actualización
            if is_new:
                log_operation(
                    'FILE_MODEL_CREATED',
                    getattr(self.uploaded_by, 'email', 'system'),
                    logger,
                    level='INFO',
                    file_id=self.pk,
                    filename=self.filename,
                    size_bytes=self.size_bytes,
                    extension=self.ext_upper,
                    project_id=self.phase.project.id if self.phase else None,
                    phase_id=self.phase.id if self.phase else None
                )
            else:
                log_operation(
                    'FILE_MODEL_UPDATED',
                    getattr(self.uploaded_by, 'email', 'system'),
                    logger,
                    level='DEBUG',
                    file_id=self.pk,
                    filename=self.filename,
                    size_bytes=self.size_bytes
                )
                
        except Exception as e:
            # Log error en guardado del modelo
            log_operation(
                'FILE_MODEL_SAVE_ERROR',
                getattr(self.uploaded_by, 'email', 'system'),
                logger,
                level='ERROR',
                error_code=FileErrorCodes.FILE_UPLOAD_STORAGE_ERROR,
                filename=self.filename,
                error_message=str(e)
            )
            raise
    
    def delete(self, *args, **kwargs):
        from core.error_codes import FileErrorCodes
        # FIXME: Migrar a structured_logging después del deploy
        # from core.structured_logging import log_business_event
        
        # FIXME: Función temporal hasta migrar a structured_logging
        def log_operation(*args, **kwargs):
            """Temporal stub para evitar errores durante deploy"""
            pass
        
        # Guardar información antes de eliminar
        file_info = {
            'id': self.pk,
            'filename': self.filename,
            'size_bytes': self.size_bytes,
            'extension': self.ext_upper,
            'project_id': self.phase.project.id if self.phase else None,
            'phase_id': self.phase.id if self.phase else None,
            'user_email': getattr(self.uploaded_by, 'email', 'system')
        }
        
        try:
            super().delete(*args, **kwargs)
            
            # Log exitoso de eliminación del modelo
            log_operation(
                'FILE_MODEL_DELETED',
                file_info['user_email'],
                logger,
                level='INFO',
                file_id=file_info['id'],
                filename=file_info['filename'],
                size_bytes=file_info['size_bytes'],
                extension=file_info['extension'],
                project_id=file_info['project_id'],
                phase_id=file_info['phase_id']
            )
            
        except Exception as e:
            # Log error en eliminación del modelo
            log_operation(
                'FILE_MODEL_DELETE_ERROR',
                file_info['user_email'],
                logger,
                level='ERROR',
                error_code=FileErrorCodes.FILE_MANAGEMENT_DELETE_ERROR,
                file_id=file_info['id'],
                filename=file_info['filename'],
                error_message=str(e)
            )
            raise
