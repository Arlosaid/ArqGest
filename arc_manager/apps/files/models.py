from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.projects.models import Phase
import os

def project_file_path(instance, filename):
    """
    Generate the file path for a new project file.
    Example: organizations/org_1/projects/proj_3/phases/phase_5/document.pdf
    """
    return (f'organizations/{instance.phase.project.organization.id}/'
            f'projects/{instance.phase.project.id}/'
            f'phases/{instance.phase.id}/{filename}')

class ProjectFile(models.Model):
    """Represents a file associated with a project's phase."""
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

    class Meta:
        verbose_name = _("Project File")
        verbose_name_plural = _("Project Files")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['ext_upper', 'size_bytes']),
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

    def save(self, *args, **kwargs):
        # Completar metadatos si están disponibles
        try:
            if self.file and hasattr(self.file, 'size'):
                self.size_bytes = int(getattr(self.file, 'size', 0) or 0)
        except Exception:
            pass
        try:
            name = (self.file.name if self.file else '')
            self.ext_upper = os.path.splitext(name)[1].replace('.', '').upper() if name else ''
        except Exception:
            pass
        super().save(*args, **kwargs)
