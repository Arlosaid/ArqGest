from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization, Client
import logging
import os

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
    
    # Campos financieros
    total_budget = models.DecimalField(
        _("Presupuesto Total"), 
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_("Monto total del proyecto")
    )
    budget_configured = models.BooleanField(
        _("Presupuesto Configurado"), 
        default=False,
        help_text=_("Indica si el presupuesto ha sido configurado")
    )

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
        """Calcula el progreso real del proyecto basado en las tareas completadas."""
        # Verificar si este proyecto tiene tareas
        total_tasks = Task.objects.filter(phase__project=self).count()
        if total_tasks == 0:
            return 0
        
        done_tasks = Task.objects.filter(phase__project=self, status='DONE').count()
        progress = int((done_tasks / total_tasks) * 100)
        
        return progress
    
    @property
    def progress_percentage_by_phases(self):
        """Calcula el progreso basado en las fases completadas (método anterior)."""
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
    
    # Propiedades financieras
    @property
    def total_paid(self):
        """Calcula el total pagado del proyecto con caché Redis."""
        from decimal import Decimal
        from django.core.cache import cache
        
        # Intentar obtener desde caché primero
        cache_key = f"project_total_paid:{self.id}"
        cached_total = cache.get(cache_key)
        
        if cached_total is not None:
            return Decimal(str(cached_total))
        
        # Si no está en caché, calcular y guardar
        total = self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Guardar en caché por 10 minutos
        cache.set(cache_key, float(total), 600)
        
        return total
    
    @property
    def remaining_amount(self):
        """Calcula el monto restante del proyecto."""
        if not self.total_budget:
            return None
        return self.total_budget - self.total_paid
    
    @property
    def payment_percentage(self):
        """Calcula el porcentaje pagado del proyecto."""
        if not self.total_budget or self.total_budget == 0:
            return 0
        return min(int((self.total_paid / self.total_budget) * 100), 100)
    
    @property
    def payment_status(self):
        """Determina el estado del pago para UI."""
        if not self.budget_configured:
            return 'not_configured'
        
        percentage = self.payment_percentage
        if percentage >= 100:
            return 'completed'
        elif percentage >= 80:
            return 'almost_complete'
        elif percentage >= 40:
            return 'in_progress'
        else:
            return 'started'
    
    @property
    def latest_payment(self):
        """Obtiene el último pago registrado."""
        return self.payments.order_by('-date', '-created_at').first()

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
        """Override save to add logging for critical task operations and invalidate cache."""
        is_new = self.pk is None
        status_changed = False
        
        if is_new:
            logger.info(f"Creating new task: '{self.title}' in phase {self.phase_id}")
        else:
            # Log status changes
            if hasattr(self, '_original_status') and self._original_status != self.status:
                logger.info(f"Task {self.pk} ('{self.title}') status changed from '{self._original_status}' to '{self.status}'")
                status_changed = True
            
            # Log assignment changes
            if hasattr(self, '_original_assigned_to') and self._original_assigned_to != self.assigned_to_id:
                old_user = f"User {self._original_assigned_to}" if self._original_assigned_to else "Unassigned"
                new_user = f"User {self.assigned_to_id}" if self.assigned_to_id else "Unassigned"
                logger.info(f"Task {self.pk} ('{self.title}') assignment changed from {old_user} to {new_user}")
        
        super().save(*args, **kwargs)
        
        # Invalidar cache de progreso cuando sea necesario
        if is_new or status_changed:
            from .cache_utils import (
                invalidate_project_progress_cache, 
                invalidate_project_cache,
                invalidate_user_projects_cache,
                invalidate_kanban_projects_cache
            )
            project_id = self.phase.project_id
            organization_id = self.phase.project.organization_id
            
            # Invalidar cache específico del progreso del proyecto
            invalidate_project_progress_cache(project_id)
            
            # Invalidar cache general del proyecto y dashboard
            invalidate_project_cache(organization_id, project_id)
            
            # Invalidar cache del selector de Kanban
            invalidate_kanban_projects_cache(organization_id)
        
        # Invalidar cache de proyectos accesibles cuando se asigna/desasigna
        assignment_changed = hasattr(self, '_original_assigned_to') and self._original_assigned_to != self.assigned_to_id
        if assignment_changed:
            from .cache_utils import invalidate_user_accessible_projects_cache
            organization_id = self.phase.project.organization_id
            
            # Invalidar cache del usuario anterior (si había uno)
            if hasattr(self, '_original_assigned_to') and self._original_assigned_to:
                invalidate_user_accessible_projects_cache(self._original_assigned_to, organization_id)
            
            # Invalidar cache del usuario nuevo (si hay uno)
            if self.assigned_to_id:
                invalidate_user_accessible_projects_cache(self.assigned_to_id, organization_id)
        
        if is_new:
            logger.info(f"Task created successfully - ID: {self.pk}, Title: '{self.title}', Phase: {self.phase_id}")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = getattr(self, 'status', None)
        self._original_assigned_to = getattr(self, 'assigned_to_id', None)
    
    def delete(self, *args, **kwargs):
        """Override delete to invalidate cache when task is deleted."""
        from .cache_utils import invalidate_project_progress_cache, invalidate_project_cache
        
        project_id = self.phase.project_id
        organization_id = self.phase.project.organization_id
        
        super().delete(*args, **kwargs)
        
        # Invalidar cache después de eliminar
        invalidate_project_progress_cache(project_id)
        invalidate_project_cache(organization_id, project_id)
        
        logger.info(f"Task deleted - ID: {self.pk}, Title: '{self.title}', Project: {project_id}")
    
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


def payment_receipt_upload_path(instance, filename):
    """Ruta organizada para comprobantes de pago.
    organizations/<org_id>/projects/<project_id>/payments/<filename>
    """
    try:
        org_id = instance.project.organization.id
        project_id = instance.project.id
    except Exception:
        org_id = 'unknown_org'
        project_id = 'unknown_project'
    safe_filename = os.path.basename(filename)
    return f"organizations/{org_id}/projects/{project_id}/payments/{safe_filename}"


class ProjectPayment(models.Model):
    """Representa un pago realizado para un proyecto."""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_("Proyecto")
    )
    amount = models.DecimalField(
        _("Monto"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Monto del pago realizado")
    )
    date = models.DateField(
        _("Fecha del Pago"),
        help_text=_("Fecha en que se realizó el pago")
    )
    description = models.TextField(
        _("Descripción"),
        blank=True,
        help_text=_("Descripción opcional del pago")
    )
    receipt_file = models.FileField(
        _("Comprobante (archivo)"),
        upload_to=payment_receipt_upload_path,
        null=True,
        blank=True,
        help_text=_("Archivo del comprobante del pago (opcional)")
    )
    receipt = models.ForeignKey(
        'files.ProjectFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_receipts',
        verbose_name=_("Comprobante"),
        help_text=_("Comprobante del pago (opcional)")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments',
        verbose_name=_("Creado por")
    )
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Pago de Proyecto")
        verbose_name_plural = _("Pagos de Proyecto")
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['project', '-date']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.project.name} - ${self.amount} ({self.date})"
    
    @property
    def percentage_of_total(self):
        """Calcula qué porcentaje del presupuesto total representa este pago."""
        if not self.project.total_budget or self.project.total_budget == 0:
            return 0
        return round((self.amount / self.project.total_budget) * 100, 1)
    
    def save(self, *args, **kwargs):
        """Override save para logging y invalidación de caché."""
        is_new = self.pk is None
        
        if is_new:
            logger.info(
                f"Creating payment: ${self.amount} for project '{self.project.name}' "
                f"({self.project.id}) on {self.date}"
            )
        
        super().save(*args, **kwargs)
        
        if is_new:
            logger.info(f"Payment created successfully - ID: {self.pk}")
        
        # OPTIMIZACIÓN: Invalidar caché financiero después de guardar
        from django.core.cache import cache
        cache.delete(f"project_total_paid:{self.project.id}")
        cache.delete(f"project_finance_stats:{self.project.id}")
        cache.delete_pattern(f"org_finance_stats:{self.project.organization.id}")
    
    def delete(self, *args, **kwargs):
        """Override delete para logging e invalidación de caché."""
        logger.info(
            f"Deleting payment: ${self.amount} from project '{self.project.name}' "
            f"({self.project.id}) - Payment ID: {self.pk}"
        )
        
        # OPTIMIZACIÓN: Invalidar caché financiero antes de eliminar
        from django.core.cache import cache
        cache.delete(f"project_total_paid:{self.project.id}")
        cache.delete(f"project_finance_stats:{self.project.id}")
        cache.delete_pattern(f"org_finance_stats:{self.project.organization.id}")
        
        super().delete(*args, **kwargs)
