from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization, Client
import logging

logger = logging.getLogger(__name__)


class Project(models.Model):
    """Representa un proyecto de arquitectura."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Activo')
        ARCHIVED = 'ARCHIVED', _('Archivado')
        COMPLETED = 'COMPLETED', _('Completado')


    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_("Organización")
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='owned_projects',
        verbose_name=_("Propietario"),
        null=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name=_("Cliente")
    )
    name = models.CharField(_("Nombre del Proyecto"), max_length=255, db_index=True)
    status = models.CharField(
        _("Estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )
    start_date = models.DateField(_("Fecha de Inicio"), null=True, blank=True)
    end_date = models.DateField(_("Fecha de Fin"), null=True, blank=True)
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Proyecto")
        verbose_name_plural = _("Proyectos")
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to add logging for critical operations."""
        is_new = self.pk is None
        
        if is_new:
            logger.info(f"Creating new project: '{self.name}' for organization {self.organization_id}")
        else:
            # Log status changes
            if hasattr(self, '_original_status') and self._original_status != self.status:
                logger.info(f"Project {self.pk} status changed from '{self._original_status}' to '{self.status}'")
        
        super().save(*args, **kwargs)
        
        if is_new:
            logger.info(f"Project created successfully - ID: {self.pk}, Name: '{self.name}'")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    @property
    def progress_percentage(self):
        """Calcula el progreso real del proyecto basado en las fases completadas."""
        total_phases = self.phases.count()
        if total_phases == 0:
            return 0
        
        completed_phases = self.phases.filter(status='COMPLETED').count()
        return int((completed_phases / total_phases) * 100)
    
    @property
    def active_phases_count(self):
        """Cuenta las fases que están en progreso."""
        return self.phases.filter(status='IN_PROGRESS').count()
    
    @property
    def pending_tasks_count(self):
        """Cuenta las tareas pendientes en todo el proyecto."""
        return Task.objects.filter(
            phase__project=self,
            status__in=['TODO', 'IN_PROGRESS', 'PAUSED']
        ).count()
    
    @property
    def total_tasks_count(self):
        """Cuenta el total de tareas en el proyecto."""
        return Task.objects.filter(phase__project=self).count()
    
    @property
    def next_deadline(self):
        """Obtiene la próxima fecha límite de tareas pendientes."""
        next_task = Task.objects.filter(
            phase__project=self,
            status__in=['TODO', 'IN_PROGRESS', 'PAUSED'],
            due_date__isnull=False
        ).order_by('due_date').first()
        
        return next_task.due_date if next_task else None

class Phase(models.Model):
    """Representa una fase dentro de un proyecto, ej., Diseño Preliminar."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        IN_PROGRESS = 'IN_PROGRESS', _('En Progreso')
        COMPLETED = 'COMPLETED', _('Completado')

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name=_("Proyecto")
    )
    name = models.CharField(_("Nombre de la Fase"), max_length=255)
    status = models.CharField(
        _("Estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    order = models.PositiveIntegerField(_("Orden"))
    start_date = models.DateField(_("Fecha de Inicio"), null=True, blank=True)
    end_date = models.DateField(_("Fecha de Fin"), null=True, blank=True)
    notes = models.TextField(_("Notas"), blank=True)
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Fase")
        verbose_name_plural = _("Fases")
        ordering = ['project', 'order']

    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Override save to add logging for status changes."""
        is_new = self.pk is None
        
        if is_new:
            logger.info(f"Creating new phase: '{self.name}' for project {self.project_id}")
        else:
            # Log status changes
            if hasattr(self, '_original_status') and self._original_status != self.status:
                logger.info(f"Phase {self.pk} ('{self.name}') status changed from '{self._original_status}' to '{self.status}'")
        
        super().save(*args, **kwargs)
        
        if is_new:
            logger.info(f"Phase created successfully - ID: {self.pk}, Name: '{self.name}', Project: {self.project_id}")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = getattr(self, 'status', None)

class Task(models.Model):
    """Representa una tarea específica dentro de una fase."""

    class Status(models.TextChoices):
        TODO = 'TODO', _('Por Hacer')
        IN_PROGRESS = 'IN_PROGRESS', _('En Progreso')
        PAUSED = 'PAUSED', _('En Pausa')
        DONE = 'DONE', _('Hecho')

    class Priority(models.TextChoices):
        LOW = 'LOW', _('Baja')
        MEDIUM = 'MEDIUM', _('Media')
        HIGH = 'HIGH', _('Alta')

    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_("Fase")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name=_("Asignado a")
    )
    title = models.CharField(_("Título de la Tarea"), max_length=255)
    description = models.TextField(_("Descripción"), blank=True)
    status = models.CharField(
        _("Estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        db_index=True
    )
    priority = models.CharField(
        _("Prioridad"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True
    )
    due_date = models.DateField(_("Fecha de Vencimiento"), null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Tarea")
        verbose_name_plural = _("Tareas")
        ordering = ['due_date', 'priority']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Override save to add logging for critical task operations."""
        is_new = self.pk is None
        
        if is_new:
            logger.info(f"Creating new task: '{self.title}' in phase {self.phase_id}")
        else:
            # Log status changes
            if hasattr(self, '_original_status') and self._original_status != self.status:
                logger.info(f"Task {self.pk} ('{self.title}') status changed from '{self._original_status}' to '{self.status}'")
            
            # Log assignment changes
            if hasattr(self, '_original_assigned_to') and self._original_assigned_to != self.assigned_to_id:
                old_user = f"User {self._original_assigned_to}" if self._original_assigned_to else "Unassigned"
                new_user = f"User {self.assigned_to_id}" if self.assigned_to_id else "Unassigned"
                logger.info(f"Task {self.pk} ('{self.title}') assignment changed from {old_user} to {new_user}")
        
        super().save(*args, **kwargs)
        
        if is_new:
            logger.info(f"Task created successfully - ID: {self.pk}, Title: '{self.title}', Phase: {self.phase_id}")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = getattr(self, 'status', None)
        self._original_assigned_to = getattr(self, 'assigned_to_id', None)
    
    @property
    def is_due_soon(self):
        """Devuelve True si la tarea vence en los próximos 3 días."""
        if not self.due_date:
            return False
        from datetime import date, timedelta
        return self.due_date <= date.today() + timedelta(days=3)

class PhaseTemplate(models.Model):
    name = models.CharField(_("Nombre"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='phase_templates',
        null=True,
        blank=True,
        verbose_name=_("Organización")
    )
    phases = models.JSONField(_("Fases"), default=list, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Plantilla de Fase")
        verbose_name_plural = _("Plantillas de Fase")
