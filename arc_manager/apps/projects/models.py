from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

def project_file_path(instance, filename):
    """
    Generate the file path for a new project file.
    Example: project_1/phase_3/document.pdf
    """
    return f'projects/{instance.phase.project.id}/phase_{instance.phase.id}/{filename}'

class Project(models.Model):
    """Represents an architectural project."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_("Owner")
    )
    name = models.CharField(_("Project Name"), max_length=255)
    client = models.CharField(_("Client Name"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Phase(models.Model):
    """Represents a phase within a project, e.g., Preliminary Design."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name=_("Project")
    )
    name = models.CharField(_("Phase Name"), max_length=255)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    order = models.PositiveIntegerField(_("Order"))
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Phase")
        verbose_name_plural = _("Phases")
        ordering = ['project', 'order']

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class Task(models.Model):
    """Represents a specific task within a phase."""

    class Status(models.TextChoices):
        TODO = 'TODO', _('Por Hacer')
        IN_PROGRESS = 'IN_PROGRESS', _('En Progreso')
        PAUSED = 'PAUSED', _('En Pausa')
        DONE = 'DONE', _('Terminado')

    class Priority(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')

    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_("Phase")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name=_("Assigned To")
    )
    title = models.CharField(_("Task Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.TODO
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ['due_date', 'priority']

    def __str__(self):
        return self.title

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
    uploaded_at = models.DateTimeField(_("Upload Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Project File")
        verbose_name_plural = _("Project Files")
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.file.name

class ProjectTemplate(models.Model):
    """
    Represents a template for creating new projects.
    Includes a predefined set of phases.
    """
    name = models.CharField(_("Template Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Project Template")
        verbose_name_plural = _("Project Templates")

    def __str__(self):
        return self.name

class PhaseTemplate(models.Model):
    """Represents a phase within a project template."""
    project_template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.CASCADE,
        related_name='phase_templates'
    )
    name = models.CharField(_("Phase Name"), max_length=100)
    order = models.PositiveIntegerField(_("Order"))

    class Meta:
        verbose_name = _("Phase Template")
        verbose_name_plural = _("Phase Templates")
        ordering = ['project_template', 'order']

    def __str__(self):
        return f"{self.project_template.name} - Phase: {self.name}"
