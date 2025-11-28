from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization, Client
import logging
import os

logger = logging.getLogger(__name__)


class ProjectManager(models.Manager):
    """Manager optimizado para Project con queries eficientes"""
    
    def with_payments(self):
        """
        OPTIMIZACIÓN: Prefetch de pagos para evitar N+1 queries
        Usar en listados donde se necesite total_paid
        """
        return self.prefetch_related('payments')
    
    def with_complete_data(self):
        """
        OPTIMIZACIÓN: Query completa para listados con toda la información
        """
        return self.select_related(
            'client', 
            'owner', 
            'organization'
        ).prefetch_related(
            'payments',
            'phases',
        )
    
    def active_for_organization(self, organization_id):
        """Proyectos activos de una organización (query optimizada)"""
        return self.filter(
            organization_id=organization_id,
            status='ACTIVE'
        ).select_related('client', 'owner')
    
    def with_financial_data(self):
        """
        OPTIMIZACIÓN: Para módulo financiero - incluye pagos
        """
        from django.db.models import Sum, Count
        return self.select_related('client', 'owner').annotate(
            payments_count=Count('payments'),
            total_paid_calculated=Sum('payments__amount')
        )


class Project(models.Model):
    """Representa un proyecto de arquitectura."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Activo')
        ARCHIVED = 'ARCHIVED', _('Archivado')
        COMPLETED = 'COMPLETED', _('Completado')

    # OPTIMIZACIÓN: Manager personalizado
    objects = ProjectManager()

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_("Organización")
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        verbose_name=_("Propietario"),
        help_text=_("El proyecto se eliminará si se elimina el propietario")
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name=_("Cliente")
    )
    name = models.CharField(
        _("Nombre del Proyecto"), 
        max_length=100, 
        db_index=True,
        help_text=_("Máximo 100 caracteres. Sea claro y específico.")
    )
    description = models.TextField(
        _("Descripción"),
        blank=True,
        null=True,
        help_text=_("Descripción detallada del proyecto")
    )
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
        indexes = [
            # OPTIMIZACIÓN: Índice compuesto para listado por organización y estado
            models.Index(fields=['organization', 'status', '-created_at'], name='project_org_status_idx'),
            # OPTIMIZACIÓN: Índice para búsquedas por organización y nombre
            models.Index(fields=['organization', 'name'], name='project_org_name_idx'),
            # OPTIMIZACIÓN: Índice para filtros financieros
            models.Index(fields=['organization', 'budget_configured', '-created_at'], name='project_budget_idx'),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save method."""
        super().save(*args, **kwargs)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    @property
    def progress_percentage(self):
        """
        Calcula el progreso real del proyecto basado en las tareas completadas.
        
        OPTIMIZACIÓN: Usa caché para evitar recalcular en cada acceso.
        En listados, usa get_or_set_dashboard_projects_progress() desde cache_utils.
        """
        from django.core.cache import cache
        
        # OPTIMIZACIÓN: Intentar obtener desde cache primero
        cache_key = f"project_progress:{self.id}"
        progress = cache.get(cache_key)
        
        if progress is not None:
            return progress
        
        # Si no está en caché, calcular
        from django.db.models import Count, Q
        stats = Task.objects.filter(phase__project=self).aggregate(
            total=Count('id'),
            done=Count('id', filter=Q(status='DONE'))
        )
        
        if stats['total'] == 0:
            progress = 0
        else:
            progress = int((stats['done'] / stats['total']) * 100)
        
        # Guardar en caché por 10 minutos
        cache.set(cache_key, progress, 600)
        
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
        """
        Calcula el total pagado del proyecto con caché Redis.
        
        OPTIMIZACIÓN: Para evitar N+1 queries en listados, usa el método estático
        get_projects_with_payments() que hace prefetch de pagos.
        """
        from decimal import Decimal
        from django.core.cache import cache
        
        # OPTIMIZACIÓN: Si ya tenemos los pagos prefetchados, usar esos
        if hasattr(self, '_prefetched_objects_cache') and 'payments' in self._prefetched_objects_cache:
            # Calcular desde los pagos prefetchados (sin query adicional)
            total = sum(payment.amount for payment in self.payments.all())
            return Decimal(str(total))
        
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
    name = models.CharField(
        _("Nombre de la Fase"), 
        max_length=100,
        help_text=_("Máximo 100 caracteres")
    )
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
        indexes = [
            # OPTIMIZACIÓN: Índice para ordenamiento por proyecto
            models.Index(fields=['project', 'order'], name='phase_project_order_idx'),
            # OPTIMIZACIÓN: Índice para filtros por estado
            models.Index(fields=['project', 'status'], name='phase_project_status_idx'),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Override save to add logging for status changes."""
        from core.structured_logging import log_info
        
        is_new = self.pk is None
        
        # Solo loguear cambios de estado, no creación (es ruido)
        if not is_new and hasattr(self, '_original_status') and self._original_status != self.status:
            # Obtener display names para los estados
            old_status_display = dict(Phase.Status.choices).get(self._original_status, self._original_status)
            new_status_display = dict(Phase.Status.choices).get(self.status, self.status)
            
            changes = [{
                'field': 'status',
                'field_label': 'Estado',
                'old': old_status_display,
                'new': new_status_display
            }]
            
            # DEBUG: Cambios de estado de fase son operaciones frecuentes
            # Solo loguear en DEBUG para trazabilidad sin ruido en producción
            logger = logging.getLogger('apps.projects')
            logger.debug(
                f"Phase '{self.name}' status: {old_status_display} -> {new_status_display}",
                extra={
                    'event': 'PHASE_STATUS_CHANGED',
                    'phase_id': self.pk,
                    'phase_name': self.name,
                    'project_id': self.project_id,
                    'old_status': old_status_display,
                    'new_status': new_status_display
                }
            )
        
        super().save(*args, **kwargs)
    
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
    title = models.CharField(
        _("Título de la Tarea"), 
        max_length=120,
        help_text=_("Máximo 120 caracteres. Sea breve y descriptivo.")
    )
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
        indexes = [
            # OPTIMIZACIÓN: Índice compuesto para listado de tareas por fase
            models.Index(fields=['phase', 'status', 'due_date'], name='task_phase_status_idx'),
            # OPTIMIZACIÓN: Índice para tareas asignadas a usuario
            models.Index(fields=['assigned_to', 'status', 'due_date'], name='task_assigned_status_idx'),
            # OPTIMIZACIÓN: Índice para cálculo de progreso
            models.Index(fields=['phase', 'status'], name='task_progress_idx'),
            # OPTIMIZACIÓN: Índice para tareas vencidas
            models.Index(fields=['due_date', 'status'], name='task_due_status_idx'),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Override save to add logging for critical task operations and invalidate cache."""
        from core.structured_logging import log_info
        
        is_new = self.pk is None
        status_changed = False
        changes = []
        
        # Solo loguear cambios importantes, no creación de cada tarea
        if not is_new:
            # Log status changes con formato estructurado
            if hasattr(self, '_original_status') and self._original_status != self.status:
                old_status_display = dict(Task.Status.choices).get(self._original_status, self._original_status)
                new_status_display = dict(Task.Status.choices).get(self.status, self.status)
                
                changes.append({
                    'field': 'status',
                    'field_label': 'Estado',
                    'old': old_status_display,
                    'new': new_status_display
                })
                status_changed = True
            
            # Log assignment changes solo cuando es relevante
            if hasattr(self, '_original_assigned_to') and self._original_assigned_to != self.assigned_to_id:
                old_user = None
                new_user = None
                
                if self._original_assigned_to:
                    try:
                        from apps.accounts.models import User
                        old_user = User.objects.get(id=self._original_assigned_to)
                    except User.DoesNotExist:
                        pass
                
                if self.assigned_to_id:
                    new_user = self.assigned_to
                
                changes.append({
                    'field': 'assigned_to',
                    'field_label': 'Asignado a',
                    'old': old_user.email if old_user else 'Sin asignar',
                    'new': new_user.email if new_user else 'Sin asignar'
                })
            
            # Log cambios si hay - DEBUG: Cambios de tarea son operaciones frecuentes
            if changes:
                task_logger = logging.getLogger('apps.projects')
                task_logger.debug(
                    f"Task '{self.title}' updated: {len(changes)} change(s)",
                    extra={
                        'event': 'TASK_CHANGED',
                        'task_id': self.pk,
                        'task_title': self.title,
                        'phase_id': self.phase_id,
                        'project_id': self.phase.project_id,
                        'changes_count': len(changes)
                    }
                )
        
        super().save(*args, **kwargs)
        
        # Invalidar cache de progreso cuando sea necesario
        if is_new or status_changed:
            from .cache_utils import (
                invalidate_project_progress_cache, 
                invalidate_project_cache,
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
            # DEBUG: Creación de tareas es operación rutinaria
            logger.debug(f"Task created - ID: {self.pk}, Title: '{self.title}', Phase: {self.phase_id}")
    
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
        
        # DEBUG: Eliminación de tareas es operación rutinaria
        logger.debug(f"Task deleted - ID: {self.pk}, Title: '{self.title}', Project: {project_id}")
    
    @property
    def is_overdue(self):
        """Devuelve True si la tarea está vencida y no completada."""
        if not self.due_date or self.status == self.Status.DONE:
            return False
        from datetime import date
        return self.due_date < date.today()

    @property
    def is_due_soon(self):
        """Devuelve True si la tarea vence en los próximos 3 días."""
        if not self.due_date:
            return False
        from datetime import date, timedelta
        return self.due_date <= date.today() + timedelta(days=3)

class PhaseTemplate(models.Model):
    name = models.CharField(
        _("Nombre"), 
        max_length=100,
        help_text=_("Máximo 100 caracteres")
    )
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
        ordering = ['name']  # Ordenar alfabéticamente por nombre


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
            # OPTIMIZACIÓN: Índice para listado de pagos por proyecto
            models.Index(fields=['project', '-date'], name='payment_project_date_idx'),
            # OPTIMIZACIÓN: Índice para pagos recientes
            models.Index(fields=['-created_at'], name='payment_created_idx'),
            # OPTIMIZACIÓN: Índice para cálculo de totales
            models.Index(fields=['project', 'amount'], name='payment_project_amount_idx'),
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
        
        super().save(*args, **kwargs)
        
        # Solo loguear creación exitosa (evento de negocio importante para auditoría)
        if is_new:
            logger.info(f"Payment #{self.pk} created: ${self.amount} for project {self.project.id}")
        
        # OPTIMIZACIÓN: Invalidar caché financiero después de guardar
        from django.core.cache import cache
        from .finance_cache import safe_delete_pattern
        cache.delete(f"project_total_paid:{self.project.id}")
        cache.delete(f"project_finance_stats:{self.project.id}")
        safe_delete_pattern(f"org_finance_stats:{self.project.organization.id}")
    
    def delete(self, *args, **kwargs):
        """Override delete para logging e invalidación de caché."""
        payment_id = self.pk
        project_id = self.project.id
        amount = self.amount
        org_id = self.project.organization.id
        
        # OPTIMIZACIÓN: Invalidar caché financiero antes de eliminar
        from django.core.cache import cache
        from .finance_cache import safe_delete_pattern
        cache.delete(f"project_total_paid:{project_id}")
        cache.delete(f"project_finance_stats:{project_id}")
        safe_delete_pattern(f"org_finance_stats:{org_id}")
        
        super().delete(*args, **kwargs)
        
        # Log eliminación (evento de negocio importante para auditoría)
        logger.info(f"Payment #{payment_id} deleted: ${amount} from project {project_id}")
