from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.projects.models import Phase

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

    class Meta:
        verbose_name = _("Project File")
        verbose_name_plural = _("Project Files")
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.file.name

    @property
    def size(self):
        """Returns the file size in a human-readable format."""
        if self.file and hasattr(self.file, 'size'):
            return self.file.size
        return 0
