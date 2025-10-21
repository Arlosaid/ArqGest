from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import logging
import time
from datetime import datetime
import os
from django.core.files.storage import default_storage
from .models import Project, Task, Phase, PhaseTemplate, ProjectPayment
from core.error_codes import (
    log_operation, 
    TaskErrorCodes, 
    ProjectErrorCodes,
    log_performance_warning
)

# Enhanced logging helper with error codes
def log_task_operation(operation, user_email, error_code=None, level='INFO', **kwargs):
    """Enhanced task operation logging with structured error codes"""
    return log_operation(operation, user_email, logger, level=level, error_code=error_code, **kwargs)

def log_project_operation(operation, user_email, error_code=None, level='INFO', **kwargs):
    """Enhanced project operation logging with structured error codes"""
    return log_operation(operation, user_email, logger, level=level, error_code=error_code, **kwargs)
from apps.files.models import ProjectFile
from .forms import ProjectForm, TaskForm, PhaseTemplateForm, PhaseFormSet
from .services import create_phases_for_project  # Importar el nuevo servicio
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from datetime import datetime
import json
from django.utils import timezone
from core.mixins import PageSizeMixin, ProjectPageSizeMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from apps.orgs.mixins import OrganizationAdminMixin
from django.core.exceptions import PermissionDenied

# Configure logger
logger = logging.getLogger(__name__)

# Project Views
class ProjectListView(LoginRequiredMixin, ProjectPageSizeMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 8

    def get_queryset(self):
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            from django.db.models import Case, When, Value, IntegerField
            from .cache_utils import get_or_set_user_accessible_projects
            
            # CONSISTENCIA: Usuarios comunes solo ven proyectos donde están asignados o son owners
            # Admins ven todos los proyectos
            if self.request.user.is_org_admin:
                # Admins ven todos los proyectos de la organización
                queryset = Project.objects.with_complete_data().filter(
                    organization=self.request.user.organization
                )
            else:
                # Usuarios comunes: solo proyectos accesibles (mismo criterio que Kanban)
                accessible_data = get_or_set_user_accessible_projects(
                    self.request.user.id,
                    self.request.user.organization.id,
                    is_admin=False
                )
                
                # Combinar IDs accesibles
                all_accessible_ids = (
                    accessible_data['active_ids'] | 
                    accessible_data['completed_ids'] | 
                    accessible_data['archived_ids']
                )
                
                queryset = Project.objects.with_complete_data().filter(
                    id__in=all_accessible_ids,
                    organization=self.request.user.organization
                )
            
            # Filtro de status (activo/archivado)
            status_filter = self.request.GET.get('status', '').strip()
            if status_filter == 'active':
                queryset = queryset.filter(status=Project.Status.ACTIVE)
                # Ordenar activos por fecha de entrega (end_date) y luego por creación
                return queryset.order_by('end_date', '-created_at')
            elif status_filter == 'archived':
                queryset = queryset.filter(status=Project.Status.ARCHIVED)
                # Ordenar archivados por fecha de creación
                return queryset.order_by('-created_at')
            
            # Si es 'all' o vacío: mostrar activos primero, luego completados, archivados al final
            # Filtro de búsqueda
            search = self.request.GET.get('search', '').strip()
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(client__name__icontains=search)
                )
            
            # Ordenamiento: Activos primero (ordenados por end_date), luego completados, archivados al final
            queryset = queryset.annotate(
                status_order=Case(
                    When(status='ACTIVE', then=Value(1)),
                    When(status='COMPLETED', then=Value(2)),
                    When(status='ARCHIVED', then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField()
                )
            ).order_by('status_order', 'end_date', '-created_at')
            
            return queryset
        logger.warning(f"User {self.request.user.email} accessed project list without organization")
        return Project.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            org_id = self.request.user.organization.id
            is_admin = self.request.user.is_org_admin
            
            # Indicar si el usuario tiene vista limitada
            context['is_limited_view'] = not is_admin
            context['is_admin'] = is_admin
            
            if is_admin:
                # Admins ven estadísticas de todos los proyectos
                cache_key = f"project_list_stats:{org_id}"
                project_stats = cache.get(cache_key)
                
                if project_stats is None:
                    projects_all = Project.objects.filter(organization=self.request.user.organization)
                    # Contadores por estado básicos
                    project_stats = {
                        'total_projects': projects_all.count(),
                        'active_projects_count': 0,
                        'completed_projects_count': 0,
                        'archived_projects_count': 0
                    }
                    try:
                        project_stats['active_projects_count'] = projects_all.filter(status='ACTIVE').count()
                        project_stats['completed_projects_count'] = projects_all.filter(status='COMPLETED').count()
                        project_stats['archived_projects_count'] = projects_all.filter(status='ARCHIVED').count()
                    except Exception:
                        # Si el modelo no tiene estos estados, usar valores por defecto
                        pass
                    
                    # Cache por 5 minutos
                    cache.set(cache_key, project_stats, 300)
                
                context.update(project_stats)
            else:
                # Usuarios comunes ven solo estadísticas de sus proyectos accesibles
                from .cache_utils import get_or_set_user_accessible_projects
                accessible_data = get_or_set_user_accessible_projects(
                    self.request.user.id,
                    org_id,
                    is_admin=False
                )
                
                project_stats = {
                    'total_projects': accessible_data['total_count'],
                    'active_projects_count': accessible_data['active_count'],
                    'completed_projects_count': accessible_data['completed_count'],
                    'archived_projects_count': accessible_data['archived_count']
                }
                context.update(project_stats)
            
            # Optimizar progreso para los proyectos de la página actual
            if 'projects' in context and context['projects']:
                from .cache_utils import get_or_set_dashboard_projects_progress
                projects_progress = get_or_set_dashboard_projects_progress(org_id)
                
                # Asignar progreso desde cache a cada proyecto
                for project in context['projects']:
                    project._cached_progress = projects_progress.get(project.id, 0)
            
            # Parámetros de filtros actuales para preservar en paginación
            current_filters = {
                'status': self.request.GET.get('status', ''),
                'search': self.request.GET.get('search', ''),
            }
            
            # Construir extra_params para el partial de paginación (preserva filtros)
            params = self.request.GET.copy()
            params.pop('page', None)
            extra_params = params.urlencode()
            if extra_params:
                extra_params = f"{extra_params}&"
            
            context['current_filters'] = current_filters
            context['extra_params'] = extra_params
        
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            from .cache_utils import get_or_set_user_accessible_projects
            
            # CONSISTENCIA: Verificar acceso del usuario al proyecto
            if self.request.user.is_org_admin:
                # Admins pueden ver todos los proyectos
                return super().get_queryset().filter(
                    organization=self.request.user.organization
                ).select_related('client', 'owner').prefetch_related('payments')
            else:
                # Usuarios comunes: solo proyectos donde están asignados o son owners
                accessible_data = get_or_set_user_accessible_projects(
                    self.request.user.id,
                    self.request.user.organization.id,
                    is_admin=False
                )
                
                # Combinar IDs accesibles
                all_accessible_ids = (
                    accessible_data['active_ids'] | 
                    accessible_data['completed_ids'] | 
                    accessible_data['archived_ids']
                )
                
                return super().get_queryset().filter(
                    id__in=all_accessible_ids,
                    organization=self.request.user.organization
                ).select_related('client', 'owner').prefetch_related('payments')
        
        logger.warning(f"User {self.request.user.email} attempted to access project detail without organization")
        return super().get_queryset().none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Indicar permisos del usuario
        is_admin = self.request.user.is_org_admin
        context['is_admin'] = is_admin
        context['is_limited_view'] = not is_admin
        context['can_view_finance'] = is_admin  # Solo admins ven finanzas
        
        # Obtener fases del proyecto con sus archivos y tareas (optimizado)
        phases = project.phases.prefetch_related(
            'files__uploaded_by',
            'tasks', 'tasks__assigned_to'
        ).order_by('order')
        
        # Archivos del proyecto
        files = ProjectFile.objects.filter(phase__project=project).select_related('phase', 'uploaded_by')
        
        from datetime import date, timedelta
        # Fases (todas) para selects y otros usos
        context['phases'] = phases
        context['files'] = files
        context['today'] = date.today()
        context['open_phase'] = self.request.GET.get('open_phase')

        # Helpers de paginación locales
        def build_page(qs, per_page, page_param_name):
            paginator = Paginator(qs, per_page)
            page_number = self.request.GET.get(page_param_name, 1)
            try:
                return paginator.page(page_number)
            except (PageNotAnInteger, EmptyPage):
                return paginator.page(1)

        # Paginación: pestaña Fases (8 por página)
        phases_page_obj = build_page(phases, 8, 'phases_page')
        context['phases_page_obj'] = phases_page_obj

        # Simplificado: mostrar todas las fases para archivos (sin paginación)
        context['files_phases_page_obj'] = None  # Ya no necesitamos paginación

        # Centro de tareas: métricas y listas rápidas (optimizado con agregaciones)
        from django.db.models import Count, Q
        tasks_qs = Task.objects.filter(phase__project=project).select_related('phase', 'assigned_to')
        agg = tasks_qs.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status='TODO')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            paused=Count('id', filter=Q(status='PAUSED')),
            done=Count('id', filter=Q(status='DONE')),
            overdue=Count('id', filter=Q(due_date__lt=date.today())),
        )
        context['tasks_total'] = agg['total']
        context['tasks_todo'] = agg['todo']
        context['tasks_in_progress'] = agg['in_progress']
        context['tasks_paused'] = agg['paused']
        context['tasks_done'] = agg['done']
        context['tasks_overdue'] = agg['overdue']

        upcoming_limit = 7
        context['tasks_due_soon'] = list(
            tasks_qs.filter(due_date__gte=date.today(), due_date__lte=date.today() + timedelta(days=upcoming_limit))
                    .order_by('due_date')[:8]
        )
        context['tasks_recent'] = list(tasks_qs.order_by('-created_at')[:8])

        # Centro de tareas (pestaña interna): paginar 9 por página
        # El responsive se manejará con CSS/JS para mostrar 5 en mobile
        tasks_page_obj = build_page(tasks_qs.order_by('due_date', 'priority'), 9, 'tasks_page')
        context['tasks_page_obj'] = tasks_page_obj

        # Obtener usuarios de la organización para asignación (excluir solo superusuarios)
        users = []
        if hasattr(project.organization, 'users'):
            users = project.organization.users.filter(is_active=True, is_superuser=False)
        elif hasattr(project.organization, 'members'):
            users = project.organization.members.filter(is_active=True, is_superuser=False)
        
        context['users'] = users

        # Contadores por fase (para el sub-tab "Por fases") sin consultas extra
        phase_task_counts = {}
        for phase in phases:
            # Usar tareas ya prefetchadas
            phase_tasks = list(getattr(phase, 'tasks').all())
            counts = {
                'TOTAL': len(phase_tasks),
                'TODO': sum(1 for t in phase_tasks if t.status == 'TODO'),
                'IN_PROGRESS': sum(1 for t in phase_tasks if t.status == 'IN_PROGRESS'),
                'PAUSED': sum(1 for t in phase_tasks if t.status == 'PAUSED'),
                'DONE': sum(1 for t in phase_tasks if t.status == 'DONE'),
            }
            phase_task_counts[phase.id] = counts
        context['phase_task_counts'] = phase_task_counts

        # Simplificado: sin paginación de archivos, mostrar todos
        # Los archivos se cargan mediante la relación phase.files.all() en el template
        
        return context

class ProjectCreateView(LoginRequiredMixin, OrganizationAdminMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'organization'):
            kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['phase_formset'] = PhaseFormSet(self.request.POST, prefix='phases')
        else:
            context['phase_formset'] = PhaseFormSet(prefix='phases')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        phase_formset = context['phase_formset']
        creation_method = form.cleaned_data.get('phase_creation_method')
        save_as_template = form.cleaned_data.get('save_as_template')
        template_name = form.cleaned_data.get('template_name')
        total_budget = form.cleaned_data.get('total_budget')
        
        project_name = form.cleaned_data.get('name')
        org_id = self.request.user.organization.id if self.request.user.organization else 'None'

        if creation_method == 'manual' and not phase_formset.is_valid():
            logger.warning(f"Project creation failed - Invalid phase formset for project '{project_name}'")
            return self.form_invalid(form)

        form.instance.owner = self.request.user
        form.instance.organization = self.request.user.organization
        # Si se proporcionó presupuesto, marcar como configurado
        if total_budget is not None and total_budget != "":
            try:
                # Solo marcar, el valor ya viene en form.instance.total_budget
                form.instance.budget_configured = True
            except Exception:
                pass
        
        try:
            self.object = form.save()
            logger.info(f"Proyecto creado - ID: {self.object.id}, Nombre: '{project_name}', Org: {org_id}, Usuario: {self.request.user.email}")
        except IntegrityError as e:
            logger.error(f"Project creation failed - IntegrityError for '{project_name}': {str(e)}")
            form.add_error('name', _('Ya existe un proyecto con este nombre en tu organización.'))
            return self.form_invalid(form)

        try:
            create_phases_for_project(
                project=self.object,
                creation_method=creation_method,
                phase_template=form.cleaned_data.get('phase_template'),
                phase_formset=phase_formset
            )
        except Exception as e:
            logger.error(f"Phase creation failed for project {self.object.id}: {str(e)}", exc_info=True)

        # Guardar como plantilla si corresponde y el método fue manual
        if creation_method == 'manual' and save_as_template:
            try:
                from .models import PhaseTemplate
                phases_payload = []
                for f in phase_formset.forms:
                    if getattr(f, 'cleaned_data', None) and not f.cleaned_data.get('DELETE'):
                        phases_payload.append({
                            'name': f.cleaned_data.get('name'),
                            'order': int(f.cleaned_data.get('order') or 0),
                        })
                phases_payload.sort(key=lambda x: x.get('order', 0))
                PhaseTemplate.objects.create(
                    name=template_name or form.cleaned_data.get('name'),
                    description=f"Plantilla generada desde el proyecto '{form.cleaned_data.get('name')}'",
                    organization=self.request.user.organization,
                    phases=phases_payload
                )
                logger.debug(f"PhaseTemplate created from project creation for org {self.request.user.organization_id}")
            except Exception as e:
                logger.error(f"Failed to create PhaseTemplate from project creation: {e}")

        # Invalidar cache después de crear proyecto
        from .cache_utils import invalidate_project_cache, invalidate_kanban_projects_cache, invalidate_user_accessible_projects_cache
        invalidate_project_cache(self.object.organization.id, self.object.id)
        invalidate_kanban_projects_cache(self.object.organization.id)
        # Asegurar que el nuevo proyecto aparezca para el creador (owner)
        try:
            invalidate_user_accessible_projects_cache(self.request.user.id, self.object.organization.id, self.request.user.is_org_admin)
        except Exception:
            pass

        return redirect(self.get_success_url())

class ProjectUpdateView(LoginRequiredMixin, OrganizationAdminMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'organization'):
            kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)

    def form_valid(self, form):
        project_name = form.cleaned_data.get('name')
        project_id = self.object.id
        total_budget = form.cleaned_data.get('total_budget')
        
        # Actualizar budget_configured según el presupuesto
        if total_budget is not None and total_budget > 0:
            # Si se proporcionó presupuesto válido, marcar como configurado
            form.instance.budget_configured = True
        elif total_budget is None or total_budget <= 0:
            # Si se eliminó o se puso en 0, desmarcar
            form.instance.budget_configured = False
        
        try:
            result = super().form_valid(form)
            logger.info(f"Proyecto actualizado - ID: {project_id}, Nombre: '{project_name}', Usuario: {self.request.user.email}")
            
            # Invalidar cache después de actualizar proyecto (incluyendo cache financiero)
            from .cache_utils import invalidate_project_cache, invalidate_kanban_projects_cache
            from .finance_cache import invalidate_finance_cache
            invalidate_project_cache(self.object.organization.id, self.object.id)
            invalidate_kanban_projects_cache(self.object.organization.id)
            # Invalidar cache financiero siempre que se toque el presupuesto
            invalidate_finance_cache(
                organization_id=self.object.organization.id,
                project_id=self.object.id
            )
            
            return result
        except IntegrityError as e:
            logger.error(f"Project update failed for {project_id} - IntegrityError: {str(e)}")
            form.add_error('name', _('Ya existe un proyecto con este nombre en tu organización.'))
            return self.form_invalid(form)

class ProjectDeleteView(LoginRequiredMixin, OrganizationAdminMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project-list')

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        project_name = self.object.name
        project_id = self.object.id
        org_id = self.object.organization.id
        
        try:
            result = super().delete(request, *args, **kwargs)
            logger.info(f"Proyecto eliminado - ID: {project_id}, Nombre: '{project_name}', Org: {org_id}, Usuario: {request.user.email}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {str(e)}", exc_info=True)
            raise

# Phase Views
class PhaseDetailView(LoginRequiredMixin, DetailView):
    model = Phase
    template_name = 'projects/phase_detail.html'
    context_object_name = 'phase'

    def get_queryset(self):
        return super().get_queryset().filter(project__organization=self.request.user.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phase = self.get_object()
        context['project'] = phase.project
        
        # Add today for template comparisons
        from datetime import date
        context['today'] = date.today()
        
        # Get only recent tasks (limit to 5) with optimized query
        recent_tasks = phase.tasks.select_related('assigned_to').order_by('-created_at')[:5]
        total_tasks_count = phase.tasks.count()
        
        context['recent_tasks'] = recent_tasks
        context['recent_tasks_count'] = min(5, total_tasks_count)
        context['has_more_tasks'] = total_tasks_count > 5
        
        # Calculate task statistics efficiently
        if total_tasks_count > 0:
            tasks_done = phase.tasks.filter(status='DONE').count()
            context['tasks_done_count'] = tasks_done
            context['tasks_in_progress_count'] = phase.tasks.filter(status='IN_PROGRESS').count()
            context['completion_percentage'] = round((tasks_done / total_tasks_count) * 100, 1)
        else:
            context['tasks_done_count'] = 0
            context['tasks_in_progress_count'] = 0
            context['completion_percentage'] = 0
        
        return context


# Kanban View
@login_required
def project_kanban(request, pk):
    """Vista del tablero Kanban para un proyecto."""
    # CONSISTENCIA: Verificar acceso del usuario al proyecto
    if request.user.is_org_admin:
        # Admins pueden acceder a cualquier proyecto
        project = get_object_or_404(Project, pk=pk, organization=request.user.organization)
    else:
        # Usuarios comunes: verificar que tengan acceso
        from .cache_utils import get_or_set_user_accessible_projects
        
        accessible_data = get_or_set_user_accessible_projects(
            request.user.id,
            request.user.organization.id,
            is_admin=False
        )
        
        # Combinar IDs accesibles
        all_accessible_ids = (
            accessible_data['active_ids'] | 
            accessible_data['completed_ids'] | 
            accessible_data['archived_ids']
        )
        
        # Verificar que el proyecto esté en la lista de accesibles
        project = get_object_or_404(
            Project, 
            pk=pk, 
            id__in=all_accessible_ids,
            organization=request.user.organization
        )
    
    # Modo de agrupación del tablero: solo 'status' (por decisión de UX)
    group_by = request.GET.get('group_by', 'status')

    # Fases con tareas
    phases = project.phases.prefetch_related('tasks__assigned_to').order_by('order')

    # Estadísticas detalladas del proyecto (optimizado)
    from django.db.models import Count, Q
    all_tasks = Task.objects.filter(phase__project=project)
    stats = all_tasks.aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status='TODO')),
        in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
        paused=Count('id', filter=Q(status='PAUSED')),
        done=Count('id', filter=Q(status='DONE')),
    )
    total_tasks = stats['total']
    tasks_todo = stats['todo']
    tasks_in_progress = stats['in_progress']
    tasks_paused = stats['paused']
    tasks_done = stats['done']
    
    # Calcular progreso del proyecto
    if total_tasks > 0:
        project_progress = int((tasks_done / total_tasks) * 100)
    else:
        project_progress = 0

    # Soporte para agrupar por estado
    status_choices = list(Task.Status.choices)
    selected_phase_id = request.GET.get('phase_id')

    tasks_by_status = {}
    if group_by == 'status':
        base_qs = all_tasks.select_related('phase', 'assigned_to')
        if selected_phase_id:
            base_qs = base_qs.filter(phase_id=selected_phase_id)
        # Traer todas las tareas y agrupar en memoria para evitar N consultas
        tasks_list = list(base_qs)
        for code, _label in status_choices:
            filtered_tasks = [t for t in tasks_list if t.status == code]
            # Crear un diccionario con las tareas y el contador
            tasks_by_status[code] = {
                'tasks': filtered_tasks,
                'count': len(filtered_tasks)
            }

    # Obtener usuarios de la organización para asignación (excluir solo superusuarios)
    users = []
    if hasattr(project.organization, 'users'):
        users = project.organization.users.filter(is_active=True, is_superuser=False)
    elif hasattr(project.organization, 'members'):
        users = project.organization.members.filter(is_active=True, is_superuser=False)

    context = {
        'project': project,
        'phases': phases,
        'users': users,
        'group_by': group_by,
        'status_choices': status_choices,
        'selected_phase_id': int(selected_phase_id) if selected_phase_id else None,
        'tasks_by_status': tasks_by_status,
        'total_tasks': total_tasks,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_paused': tasks_paused,
        'tasks_done': tasks_done,
        'project_progress': project_progress,
        'today': timezone.now().date(),
    }

    return render(request, 'projects/kanban_board.html', context)


class ProjectPhasesEditView(LoginRequiredMixin, OrganizationAdminMixin, View):
    """Editor intuitivo de fases para un proyecto (crear/renombrar/eliminar/reordenar)."""

    template_name = 'projects/phases_edit.html'

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk, organization=request.user.organization)
        phases = list(project.phases.order_by('order').values('id', 'name', 'order'))
        # Plantillas disponibles (de la organización o globales)
        try:
            templates = PhaseTemplate.objects.filter(
                Q(organization=request.user.organization) | Q(organization__isnull=True)
            ).order_by('name')
        except Exception:
            templates = PhaseTemplate.objects.none()
        context = {
            'project': project,
            'phases': phases,
            'templates': templates,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk, organization=request.user.organization)

        try:
            payload = json.loads(request.body or '{}')
            items = payload.get('phases', [])
            template_id = payload.get('template_id')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'invalid_json'}, status=400)

        # Reemplazar por plantilla si se envía template_id
        if template_id:
            try:
                template = PhaseTemplate.objects.get(
                    pk=template_id,
                    # Asegurar pertenencia a la organización o ser global
                    organization__in=[request.user.organization, None]
                )
            except PhaseTemplate.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'template_not_found'}, status=404)

            from django.db import transaction
            try:
                with transaction.atomic():
                    # Eliminar fases existentes del proyecto
                    project.phases.all().delete()
                    # Crear nuevas fases según la plantilla
                    ordered = sorted(template.phases or [], key=lambda x: x.get('order', 0))
                    for idx, p in enumerate(ordered):
                        name = (p.get('name') or '').strip()
                        if not name:
                            continue
                        Phase.objects.create(project=project, name=name, order=idx)

                from .cache_utils import invalidate_project_cache
                invalidate_project_cache(project.organization.id, project.id)
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Failed to apply phase template for project {project.id}: {e}", exc_info=True)
                return JsonResponse({'success': False, 'error': 'unexpected_error'}, status=500)

        # Validación básica
        names = []
        for item in items:
            if item.get('delete'):
                # Eliminar no requiere nombre
                continue
            name = (item.get('name') or '').strip()
            if not name:
                return JsonResponse({'success': False, 'error': 'name_required'}, status=400)
            if name in names:
                return JsonResponse({'success': False, 'error': 'duplicate_name'}, status=400)
            names.append(name)

        # Aplicar cambios atómicos
        from django.db import transaction
        try:
            with transaction.atomic():
                existing = {p.id: p for p in project.phases.all()}

                # Procesar elementos
                for item in items:
                    phase_id = item.get('id')
                    to_delete = bool(item.get('delete'))
                    name = (item.get('name') or '').strip()
                    try:
                        order = int(item.get('order') or 0)
                    except Exception:
                        order = 0

                    if phase_id and phase_id in existing:
                        phase = existing[phase_id]
                        if to_delete:
                            phase.delete()
                        else:
                            changed = False
                            if name and phase.name != name:
                                phase.name = name
                                changed = True
                            if phase.order != order:
                                phase.order = order
                                changed = True
                            if changed:
                                phase.save()
                    else:
                        if not to_delete and name:
                            Phase.objects.create(project=project, name=name, order=order)

                # Reordenar de forma consistente (0..n)
                for idx, phase in enumerate(project.phases.order_by('order', 'id')):
                    if phase.order != idx:
                        phase.order = idx
                        phase.save()

            # Invalidar cache relacionada
            from .cache_utils import invalidate_project_cache
            invalidate_project_cache(project.organization.id, project.id)

            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Failed to update phases for project {project.id}: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'unexpected_error'}, status=500)


@login_required
def project_statistics(request, pk):
    """Devuelve estadísticas simples de tareas del proyecto en JSON."""
    project = get_object_or_404(Project, pk=pk, organization=request.user.organization)
    all_tasks = Task.objects.filter(phase__project=project)
    data = {
        'success': True,
        'total_tasks': all_tasks.count(),
        'completed_tasks': all_tasks.filter(status='DONE').count(),
        'in_progress_tasks': all_tasks.filter(status='IN_PROGRESS').count(),
        'paused_tasks': all_tasks.filter(status='PAUSED').count(),
    }
    return JsonResponse(data)

# Phase Create View
@login_required
def phase_create(request, project_pk):
    """Vista para crear una nueva fase."""
    project = get_object_or_404(Project, pk=project_pk, organization=request.user.organization)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        notes = request.POST.get('notes', '')
        order = request.POST.get('order', 1)
        
        if name:
            phase = Phase.objects.create(
                project=project,
                name=name,
                notes=notes,
                order=order
            )
            messages.success(request, f'Fase "{name}" creada exitosamente.')
            return redirect('projects:project-detail', pk=project_pk)
        else:
            messages.error(request, 'El nombre de la fase es requerido.')
    
    return redirect('projects:project-detail', pk=project_pk)

# Task Views
@login_required
def task_create(request, project_pk):
    """Crear una nueva tarea."""
    project = get_object_or_404(Project, pk=project_pk, organization=request.user.organization)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        phase_id = request.POST.get('phase')
        assigned_to_id = request.POST.get('assigned_to')
        priority = request.POST.get('priority', 'MEDIUM')
        due_date_raw = request.POST.get('due_date')
        # Parsear fecha de forma segura (YYYY-MM-DD). Si no es válida, usar None
        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, '%Y-%m-%d').date()
            except ValueError:
                due_date = None
        
        # Fallback de fase: si no viene 'phase', usar la primera fase del proyecto;
        # si no existen fases, crear una por defecto "Backlog".
        if not phase_id:
            first_phase = project.phases.order_by('order').first()
            if not first_phase:
                # Crear fase por defecto
                first_phase = Phase.objects.create(
                    project=project,
                    name='Backlog',
                    order=1
                )
            phase_id = str(first_phase.pk)

        if title and phase_id:
            try:
                phase = Phase.objects.get(pk=phase_id, project=project)
                
                task = Task.objects.create(
                    phase=phase,
                    title=title,
                    description=description,
                    priority=priority,
                    due_date=due_date if due_date else None
                )
                
                # Validar que el asignado pertenezca a la organización del proyecto
                if assigned_to_id:
                    try:
                        eligible_qs = project.organization.users.filter(
                            pk=assigned_to_id,
                            is_active=True,
                            is_superuser=False
                        )
                        assignee_exists = eligible_qs.exists()
                    except Exception:
                        assignee_exists = False
                    if assignee_exists:
                        task.assigned_to_id = assigned_to_id
                        task.save()
                    else:
                        # Si el usuario no pertenece a la organización, no asignar y reportar
                        log_msg, log_data = log_task_operation(
                            'CREATE_TASK_ERROR',
                            request.user.email,
                            project_id=project_pk,
                            assignee_id=assigned_to_id,
                            error_code=TaskErrorCodes.TASK_CREATE_INVALID_ASSIGNEE
                        )
                        logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_CREATE_INVALID_ASSIGNEE}")
                        
                        error_msg = _('El usuario seleccionado no pertenece a tu organización.')
                        messages.error(request, error_msg)
                        accepts_json = 'application/json' in request.headers.get('Accept', '')
                        is_htmx = request.headers.get('HX-Request')
                        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                        if accepts_json or is_htmx or is_ajax:
                            return JsonResponse({'success': False, 'error': 'invalid_assignee', 'error_code': TaskErrorCodes.TASK_CREATE_INVALID_ASSIGNEE}, status=400)
                
                # Si es una petición AJAX/JSON, devolver JSON sin mensaje Django
                accepts_json = 'application/json' in request.headers.get('Accept', '')
                is_htmx = request.headers.get('HX-Request')
                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if accepts_json or is_htmx or is_ajax:
                    return JsonResponse({'success': True, 'task_id': task.id})
                
                # Solo mostrar mensaje Django para peticiones normales (no AJAX)
                messages.success(request, f'Tarea "{title}" creada exitosamente.')

                # Redirecciones para peticiones normales
                if 'kanban' in request.META.get('HTTP_REFERER', ''):
                    return redirect('projects:project-kanban', pk=project_pk)
                return redirect('projects:project-detail', pk=project_pk)
                    
            except Phase.DoesNotExist:
                log_msg, log_data = log_task_operation(
                    'CREATE_TASK_ERROR',
                    request.user.email,
                    project_id=project_pk,
                    phase_id=phase_id,
                    error_code=TaskErrorCodes.TASK_CREATE_PHASE_NOT_FOUND
                )
                logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_CREATE_PHASE_NOT_FOUND}")
                messages.error(request, 'La fase seleccionada no existe.')
            except Exception as e:
                log_msg, log_data = log_task_operation(
                    'CREATE_TASK_ERROR',
                    request.user.email,
                    project_id=project_pk,
                    error_code=TaskErrorCodes.TASK_CREATE_UNEXPECTED_ERROR,
                    exception=str(e)
                )
                logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_CREATE_UNEXPECTED_ERROR}", exc_info=True)
                messages.error(request, 'Error inesperado al crear la tarea.')
        else:
            missing_fields = []
            if not title:
                missing_fields.append('title')
            if not phase_id:
                missing_fields.append('phase_id')
                
            log_msg, log_data = log_task_operation(
                'CREATE_TASK_ERROR',
                request.user.email,
                project_id=project_pk,
                missing_fields=missing_fields,
                error_code=TaskErrorCodes.TASK_CREATE_MISSING_TITLE if not title else TaskErrorCodes.TASK_CREATE_MISSING_PHASE
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_CREATE_MISSING_TITLE if not title else TaskErrorCodes.TASK_CREATE_MISSING_PHASE}")
            messages.error(request, 'El título y la fase son requeridos.')
    
    return redirect('projects:project-detail', pk=project_pk)

class TaskListView(LoginRequiredMixin, ProjectPageSizeMixin, ListView):
    paginate_by = 8
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        start_time = time.time()
        queryset = Task.objects.filter(
            phase__project__organization=self.request.user.organization
        ).exclude(
            phase__project__status='ARCHIVED'
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')
        
        query_time = time.time() - start_time
        task_count = queryset.count()
        
        # Solo loguear si hay problema de performance
        if query_time > 2.0:
            log_msg, log_data = log_task_operation(
                'LIST_ALL_TASKS',
                self.request.user.email,
                org_id=self.request.user.organization.id,
                task_count=task_count,
                query_time_ms=round(query_time * 1000, 2)
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_QUERY_SLOW}")
        elif task_count > 1000:
            log_msg, log_data = log_task_operation(
                'LIST_ALL_TASKS',
                self.request.user.email,
                org_id=self.request.user.organization.id,
                task_count=task_count,
                query_time_ms=round(query_time * 1000, 2)
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_LIST_LARGE_DATASET}")
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_tasks = Task.objects.filter(
            phase__project__organization=self.request.user.organization
        ).exclude(phase__project__status='ARCHIVED')
        context['total_tasks'] = all_tasks.count()
        context['tasks_todo'] = all_tasks.filter(status='TODO').count()
        context['tasks_in_progress'] = all_tasks.filter(status='IN_PROGRESS').count()
        context['tasks_paused'] = all_tasks.filter(status='PAUSED').count()
        context['tasks_done'] = all_tasks.filter(status='DONE').count()
        context['today'] = timezone.now().date()
        return context

class MyTaskListView(LoginRequiredMixin, ProjectPageSizeMixin, ListView):
    model = Task
    template_name = 'projects/my_tasks.html'
    context_object_name = 'tasks'
    paginate_by = 8

    def get_queryset(self):
        start_time = time.time()
        queryset = Task.objects.filter(
            phase__project__organization=self.request.user.organization,
            assigned_to=self.request.user
        ).exclude(
            phase__project__status='ARCHIVED'
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')
        
        # Aplicar filtros si están presentes
        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        search_filter = self.request.GET.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
            
        if search_filter:
            queryset = queryset.filter(
                Q(title__icontains=search_filter) | 
                Q(phase__project__name__icontains=search_filter) |
                Q(phase__name__icontains=search_filter)
            )
        
        query_time = time.time() - start_time
        task_count = queryset.count()
        
        # Solo loguear si hay problema de performance
        if query_time > 2.0:
            log_msg, log_data = log_task_operation(
                'LIST_MY_TASKS',
                self.request.user.email,
                org_id=self.request.user.organization.id,
                task_count=task_count,
                query_time_ms=round(query_time * 1000, 2),
                filters={'status': status_filter, 'priority': priority_filter, 'search': search_filter}
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_QUERY_SLOW}")
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todas las tareas del usuario sin filtros (excluir archivados)
        all_tasks = Task.objects.filter(
            phase__project__organization=self.request.user.organization,
            assigned_to=self.request.user
        ).exclude(phase__project__status='ARCHIVED')
        
        # Obtener el queryset filtrado completo (todas las páginas)
        filtered_queryset = self.get_queryset()
        
        # Verificar si hay filtros activos
        has_filters = any([
            self.request.GET.get('status'),
            self.request.GET.get('priority'), 
            self.request.GET.get('search')
        ])
        
        if has_filters:
            # Contadores basados en todas las tareas filtradas (no solo la página actual)
            context['total_tasks'] = filtered_queryset.count()
            context['tasks_todo'] = filtered_queryset.filter(status='TODO').count()
            context['tasks_in_progress'] = filtered_queryset.filter(status='IN_PROGRESS').count()
            context['tasks_paused'] = filtered_queryset.filter(status='PAUSED').count()
            context['tasks_done'] = filtered_queryset.filter(status='DONE').count()
            context['showing_filtered'] = True
            # Información adicional sobre el total sin filtros
            context['all_total_tasks'] = all_tasks.count()
            context['all_tasks_todo'] = all_tasks.filter(status='TODO').count()
            context['all_tasks_in_progress'] = all_tasks.filter(status='IN_PROGRESS').count()
            context['all_tasks_paused'] = all_tasks.filter(status='PAUSED').count()
            context['all_tasks_done'] = all_tasks.filter(status='DONE').count()
        else:
            # Sin filtros, usar todas las tareas para los contadores
            context['total_tasks'] = all_tasks.count()
            context['tasks_todo'] = all_tasks.filter(status='TODO').count()
            context['tasks_in_progress'] = all_tasks.filter(status='IN_PROGRESS').count()
            context['tasks_paused'] = all_tasks.filter(status='PAUSED').count()
            context['tasks_done'] = all_tasks.filter(status='DONE').count()
            context['showing_filtered'] = False
        
        # Construir parámetros de filtro para la paginación
        filter_params = ""
        if self.request.GET.get('status'):
            filter_params += f"status={self.request.GET.get('status')}&"
        if self.request.GET.get('priority'):
            filter_params += f"priority={self.request.GET.get('priority')}&"
        if self.request.GET.get('search'):
            filter_params += f"search={self.request.GET.get('search')}&"
        
        context['filter_params'] = filter_params
        context['today'] = timezone.now().date()
        return context

@login_required
@require_POST
def update_task_status(request, task_pk):
    """Actualizar el estado de una tarea."""
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__organization=request.user.organization)
        old_status = task.status
        
        # Soportar JSON y x-www-form-urlencoded
        status = None
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body or '{}')
                status = payload.get('status')
            except json.JSONDecodeError:
                status = None
        if status is None:
            status = request.POST.get('status')
        
        if status in dict(Task.Status.choices):
            task.status = status
            task.save()
            return JsonResponse({'success': True})
        else:
            log_msg, log_data = log_task_operation(
                'UPDATE_TASK_ERROR',
                request.user.email,
                task_id=task_pk,
                invalid_status=status,
                error_code=TaskErrorCodes.TASK_UPDATE_INVALID_STATUS
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_INVALID_STATUS}")
            return JsonResponse({'success': False, 'error': 'Estado inválido', 'error_code': TaskErrorCodes.TASK_UPDATE_INVALID_STATUS})
    except Task.DoesNotExist:
        log_msg, log_data = log_task_operation(
            'UPDATE_TASK_ERROR',
            request.user.email,
            task_id=task_pk,
            error_code=TaskErrorCodes.TASK_UPDATE_NOT_FOUND
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_NOT_FOUND}")
        return JsonResponse({'success': False, 'error': 'Tarea no encontrada', 'error_code': TaskErrorCodes.TASK_UPDATE_NOT_FOUND})
    except Exception as e:
        log_msg, log_data = log_task_operation(
            'UPDATE_TASK_ERROR',
            request.user.email,
            task_id=task_pk,
            error_code=TaskErrorCodes.TASK_UPDATE_UNEXPECTED_ERROR,
            exception=str(e)
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_UNEXPECTED_ERROR}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error inesperado', 'error_code': TaskErrorCodes.TASK_UPDATE_UNEXPECTED_ERROR})

@login_required
@require_POST
def move_task(request, task_pk):
    """Mover una tarea a otra fase."""
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__organization=request.user.organization)
        old_phase_id = task.phase.id
        old_phase_name = task.phase.name
        
        # Soportar JSON y x-www-form-urlencoded
        phase_id = None
        if request.content_type and 'application/json' in request.content_type:
            try:
                payload = json.loads(request.body or '{}')
                phase_id = payload.get('phase_id')
            except json.JSONDecodeError:
                phase_id = None
        if phase_id is None:
            phase_id = request.POST.get('phase_id')
        
        if phase_id:
            try:
                new_phase = Phase.objects.get(pk=phase_id, project=task.phase.project)
                task.phase = new_phase
                task.save()
                return JsonResponse({'success': True})
            except Phase.DoesNotExist:
                log_msg, log_data = log_task_operation(
                    'MOVE_TASK_ERROR',
                    request.user.email,
                    task_id=task_pk,
                    phase_id=phase_id,
                    error_code=TaskErrorCodes.TASK_UPDATE_INVALID_PHASE
                )
                logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_INVALID_PHASE}")
                return JsonResponse({'success': False, 'error': 'Fase no encontrada', 'error_code': TaskErrorCodes.TASK_UPDATE_INVALID_PHASE})
        else:
            log_msg, log_data = log_task_operation(
                'MOVE_TASK_ERROR',
                request.user.email,
                task_id=task_pk,
                error_code=TaskErrorCodes.TASK_UPDATE_INVALID_PHASE
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_INVALID_PHASE}")
            return JsonResponse({'success': False, 'error': 'ID de fase requerido', 'error_code': TaskErrorCodes.TASK_UPDATE_INVALID_PHASE})
    except Exception as e:
        log_msg, log_data = log_task_operation(
            'MOVE_TASK_ERROR',
            request.user.email,
            task_id=task_pk,
            error_code=TaskErrorCodes.TASK_UPDATE_UNEXPECTED_ERROR,
            exception=str(e)
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_UNEXPECTED_ERROR}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error inesperado', 'error_code': TaskErrorCodes.TASK_UPDATE_UNEXPECTED_ERROR})

@login_required
def task_edit(request, pk):
    """Editar una tarea."""
    try:
        task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
        project = task.phase.project

    except Task.DoesNotExist:
        log_msg, log_data = log_task_operation(
            'ACCESS_TASK_EDIT_ERROR',
            request.user.email,
            task_id=pk,
            error_code=TaskErrorCodes.TASK_ACCESS_NOT_FOUND
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_ACCESS_NOT_FOUND}")
        raise Http404("Tarea no encontrada")
    except Exception as e:
        log_msg, log_data = log_task_operation(
            'ACCESS_TASK_EDIT_ERROR',
            request.user.email,
            task_id=pk,
            error_code=TaskErrorCodes.TASK_ACCESS_UNAUTHORIZED,
            exception=str(e)
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_ACCESS_UNAUTHORIZED}", exc_info=True)
        raise

    if request.method == 'POST':
        # Obtener datos del formulario
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'MEDIUM')
        assigned_to_id = request.POST.get('assigned_to')
        phase_id = request.POST.get('phase')
        due_date_raw = request.POST.get('due_date')
        
        # Validar datos básicos
        if not title:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse('El título es requerido', status=400)
            messages.error(request, 'El título es requerido')
            return redirect('projects:project-detail', pk=project.id)
        
        # Procesar fecha
        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Obtener fase
        try:
            phase = project.phases.get(id=phase_id)
        except:
            phase = task.phase  # Mantener la fase actual si hay error
        
        # Obtener usuario asignado
        assigned_to = None
        if assigned_to_id:
            try:
                assigned_to = project.organization.users.get(id=assigned_to_id)
            except:
                pass
        
        # Actualizar tarea
        try:
            task.title = title
            task.description = description
            task.priority = priority
            task.assigned_to = assigned_to
            task.phase = phase
            task.due_date = due_date
            task.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse('Tarea actualizada correctamente', status=200)
            else:
                messages.success(request, 'Tarea actualizada correctamente')
                return redirect('projects:project-kanban', pk=project.id)
                
        except Exception as e:
            logger.error(f"Error al actualizar tarea {task.id}: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse('Error al guardar la tarea', status=500)
            messages.error(request, 'Error al guardar la tarea')
            return redirect('projects:project-detail', pk=project.id)


    # Para GET, mostrar formulario de edición
    context = {
        'task': task,
        'project': project,
        'phases': project.phases.all(),
        'users': project.organization.users.filter(is_active=True, is_superuser=False),
    }

    return render(request, 'projects/partials/task_edit_modal.html', context)


def get_project_color(project_id):
    """Generate a project-specific color based on project ID for consistency."""
    project_colors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
    ]
    return project_colors[project_id % len(project_colors)]

@login_required
@require_POST
def task_delete(request, pk):
    """Eliminar una tarea (JSON) - Solo admin de organización."""
    task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
    
    # Verificar que el usuario es admin de la organización
    if not hasattr(request.user, 'is_org_admin') or not request.user.is_org_admin:
        log_msg, log_data = log_task_operation(
            'DELETE_TASK_UNAUTHORIZED',
            request.user.email,
            task_id=pk,
            error_code=TaskErrorCodes.TASK_DELETE_PERMISSION_DENIED
        )
        logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_DELETE_PERMISSION_DENIED}")
        return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar tareas', 'error_code': TaskErrorCodes.TASK_DELETE_PERMISSION_DENIED}, status=403)
    
    task_title = task.title
    project_id = task.phase.project.id
    
    try:
        task.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        log_msg, log_data = log_task_operation(
            'DELETE_TASK_ERROR',
            request.user.email,
            task_id=pk,
            error_code=TaskErrorCodes.TASK_DELETE_UNEXPECTED_ERROR,
            exception=str(e)
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_DELETE_UNEXPECTED_ERROR}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error al eliminar tarea', 'error_code': TaskErrorCodes.TASK_DELETE_UNEXPECTED_ERROR})

@login_required
def project_tasks_paginated(request, project_pk):
    """Vista AJAX para cargar tareas paginadas del centro de tareas."""
    project = get_object_or_404(Project, pk=project_pk, organization=request.user.organization)
    
    # Parámetros de paginación
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 9))  # 9 desktop, 5 mobile desde JS
    
    # Filtros
    phase_filter = request.GET.get('phase', '')

    # Queryset base
    tasks_qs = Task.objects.filter(phase__project=project).select_related('phase', 'assigned_to')
    
    # Aplicar filtro de fase
    if phase_filter:
        tasks_qs = tasks_qs.filter(phase_id=phase_filter)
    
    # Ordenar
    tasks_qs = tasks_qs.order_by('due_date', 'priority')
    
    # Paginación
    paginator = Paginator(tasks_qs, per_page)
    try:
        tasks_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        tasks_page = paginator.page(1)
    
    from datetime import date
    context = {
        'project': project,
        'tasks_page_obj': tasks_page,
        'today': date.today(),
        'current_filters': {
            'phase': phase_filter,
        }
    }
    
    return render(request, 'projects/partials/tasks_paginated.html', context)

@login_required
def phase_files_paginated(request, project_id, phase_id):
    """
    Vista optimizada para cargar archivos con scroll infinito y Redis cache.
    Ultra-rápida para Railway con eliminación de bottlenecks.
    """
    from django.core.cache import cache
    from django.conf import settings
    from core.error_codes import log_operation
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        phase = get_object_or_404(Phase, id=phase_id, project_id=project_id, project__organization=request.user.organization)
    
        # Parámetros optimizados
        offset = int(request.GET.get('offset', 0))  # Usar offset en lugar de page
        limit = int(request.GET.get('limit', 20))   # Límite por batch (aumentado)
        load_more = request.GET.get('load_more', 'false') == 'true'
        
        # Filtros
        file_type_filter = request.GET.get('type', '')
        date_filter = request.GET.get('date', '')
    
        # Crear clave de cache única para esta consulta
        cache_key = f"files_phase_{phase_id}_{offset}_{limit}_{file_type_filter}_{date_filter}"
        
        # Intentar obtener desde cache Redis primero
        cached_result = cache.get(cache_key)
        
        if cached_result and not settings.DEBUG:
            # En producción, usar cache para respuesta ultra-rápida
            files_data, has_more = cached_result
            context = {
                'phase': phase,
                'files': files_data,
                'has_more': has_more,
                'current_filters': {'type': file_type_filter, 'date': date_filter},
                'next_offset': offset + limit if has_more else None,
                'load_more': load_more,
                'from_cache': True
            }
        else:
            # Query optimizada - SIN count() para evitar query lenta
            files_qs = phase.files.select_related('uploaded_by').order_by('-uploaded_at')
            
            # Aplicar filtros de forma eficiente
            if file_type_filter:
                file_types = file_type_filter.split(',')
                files_qs = files_qs.filter(ext_upper__in=[ft.upper() for ft in file_types])
            
            if date_filter:
                from datetime import datetime, timedelta
                today = datetime.now().date()
                if date_filter == 'today':
                    files_qs = files_qs.filter(uploaded_at__date=today)
                elif date_filter == 'week':
                    week_ago = today - timedelta(days=7)
                    files_qs = files_qs.filter(uploaded_at__date__gte=week_ago)
                elif date_filter == 'month':
                    month_ago = today - timedelta(days=30)
                    files_qs = files_qs.filter(uploaded_at__date__gte=month_ago)
                elif date_filter == 'older':
                    month_ago = today - timedelta(days=30)
                    files_qs = files_qs.filter(uploaded_at__date__lt=month_ago)
        
            # Query optimizada con offset/limit (más eficiente que Django Paginator)
            files_batch = list(files_qs[offset:offset + limit + 1])  # +1 para verificar si hay más
            has_more = len(files_batch) > limit
            
            if has_more:
                files_batch = files_batch[:limit]  # Remover el archivo extra
            
            # Preparar datos para caché (serializar solo lo necesario)
            files_data = []
            for file in files_batch:
                files_data.append({
                    'id': file.id,
                    'filename': file.filename,
                    'extension': file.ext_upper,
                    'size': file.size,
                    'uploaded_at': file.uploaded_at,
                    'uploaded_by_name': file.uploaded_by.get_full_name() if file.uploaded_by else 'N/A',
                    'file_url': file.file.url if file.file else None,
                })
            
            # Guardar en cache Redis (5 minutos en desarrollo, 10 en producción)
            cache_timeout = 300 if settings.DEBUG else 600
            cache.set(cache_key, (files_data, has_more), cache_timeout)
            
            context = {
                'phase': phase,
                'files': files_data,
                'has_more': has_more,
                'current_filters': {'type': file_type_filter, 'date': date_filter},
                'next_offset': offset + limit if has_more else None,
                'load_more': load_more,
                'from_cache': False
            }
    
        # Template optimizado basado en el tipo de request
        if load_more:
            # Para cargar más archivos (scroll infinito)
            return render(request, 'projects/partials/files_infinite_scroll.html', context)
        else:
            # Para carga inicial
            return render(request, 'projects/partials/files_optimized.html', context)
    
    except Exception as e:
        # Log error crítico solo en debug
        if settings.DEBUG:
            logger.error(f"Error en phase_files_paginated: {str(e)}")
        
        # Respuesta de error simplificada
        return render(request, 'projects/partials/files_error.html', {
            'phase_id': phase_id,
            'error': 'Error cargando archivos'
        })

# PhaseTemplate Views
class PhaseTemplateListView(LoginRequiredMixin, OrganizationAdminMixin, ProjectPageSizeMixin, ListView):
    paginate_by = 8
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        # Mostrar solo plantillas de la organización del usuario para gestión
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return PhaseTemplate.objects.filter(organization=self.request.user.organization)
        return PhaseTemplate.objects.none()

class PhaseTemplateCreateView(LoginRequiredMixin, OrganizationAdminMixin, CreateView):
    model = PhaseTemplate
    form_class = PhaseTemplateForm
    template_name = 'projects/phasetemplate_form.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Inicializar formset de fases
        if self.request.POST:
            context['phase_formset'] = PhaseFormSet(self.request.POST, prefix='phases')
        else:
            # Si se desea, se puede iniciar con un ejemplo vacío
            context['phase_formset'] = PhaseFormSet(prefix='phases')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        phase_formset = context['phase_formset']

        if not phase_formset.is_valid():
            return self.form_invalid(form)

        # Asociar la organización
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            form.instance.organization = self.request.user.organization

        # Persistir fases en JSON ordenadas por 'order'
        phases_payload = []
        for f in phase_formset.forms:
            if f.cleaned_data and not f.cleaned_data.get('DELETE'):
                phases_payload.append({
                    'name': f.cleaned_data.get('name'),
                    'order': int(f.cleaned_data.get('order') or 0),
                })
        phases_payload.sort(key=lambda x: x.get('order', 0))
        form.instance.phases = phases_payload

        return super().form_valid(form)

class PhaseTemplateDetailView(LoginRequiredMixin, OrganizationAdminMixin, DetailView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        # Limitar la vista de detalle a plantillas de la organización
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return PhaseTemplate.objects.filter(organization=self.request.user.organization)
        return PhaseTemplate.objects.none()

class PhaseTemplateUpdateView(LoginRequiredMixin, OrganizationAdminMixin, UpdateView):
    model = PhaseTemplate
    form_class = PhaseTemplateForm
    template_name = 'projects/phasetemplate_form.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

    def get_queryset(self):
        # Solo permitir edición de plantillas de la organización
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return PhaseTemplate.objects.filter(organization=self.request.user.organization)
        return PhaseTemplate.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.object
        if self.request.POST:
            context['phase_formset'] = PhaseFormSet(self.request.POST, prefix='phases')
        else:
            # Precargar fases existentes desde JSON
            initial = []
            try:
                for idx, p in enumerate(sorted(instance.phases or [], key=lambda x: x.get('order', 0))):
                    initial.append({'name': p.get('name', ''), 'order': p.get('order', idx)})
            except Exception:
                initial = []
            context['phase_formset'] = PhaseFormSet(prefix='phases', initial=initial)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        phase_formset = context['phase_formset']

        if not phase_formset.is_valid():
            return self.form_invalid(form)

        phases_payload = []
        for f in phase_formset.forms:
            if f.cleaned_data and not f.cleaned_data.get('DELETE'):
                phases_payload.append({
                    'name': f.cleaned_data.get('name'),
                    'order': int(f.cleaned_data.get('order') or 0),
                })
        phases_payload.sort(key=lambda x: x.get('order', 0))
        form.instance.phases = phases_payload

        return super().form_valid(form)

class PhaseTemplateDeleteView(LoginRequiredMixin, OrganizationAdminMixin, DeleteView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_confirm_delete.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)


@login_required
def task_detail(request, pk):
    """Vista para mostrar los detalles de una tarea en formato modal"""
    task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
    
    # Generate a project-specific color based on project ID for consistency
    project_colors = [
        '#3b82f6',  # Blue
        '#10b981',  # Green
        '#f59e0b',  # Yellow
        '#ef4444',  # Red
        '#8b5cf6',  # Purple
        '#06b6d4',  # Cyan
        '#f97316',  # Orange
        '#84cc16',  # Lime
        '#ec4899',  # Pink
        '#6366f1',  # Indigo
    ]
    
    project_color = project_colors[task.phase.project.id % len(project_colors)]
    
    context = {
        'task': task,
        'project': task.phase.project,
        'project_color': project_color,
        'today': timezone.now().date(),
    }
    
    return render(request, 'projects/task_detail_modal.html', context)


# Force reload

class ProjectKanbanSelectorView(LoginRequiredMixin, View):
    """Vista para seleccionar proyecto y ir al kanban"""
    template_name = 'projects/kanban_selector.html'
    
    def get(self, request):
        from .cache_utils import get_or_set_user_accessible_projects
        
        organization_id = request.user.organization.id
        is_admin = request.user.is_org_admin
        
        # SOLUCIÓN ÓPTIMA: Obtener solo proyectos accesibles desde cache
        accessible_data = get_or_set_user_accessible_projects(
            request.user.id, 
            organization_id, 
            is_admin
        )
        
        # OPTIMIZACIÓN: Construir QuerySets con datos completos para evitar N+1
        # No mostrar proyectos archivados
        active_projects = Project.objects.with_complete_data().filter(
            id__in=accessible_data['active_ids']
        ).order_by('-created_at')
        
        completed_projects = Project.objects.with_complete_data().filter(
            id__in=accessible_data['completed_ids']
        ).order_by('-created_at')

        # Paginación por sección (8 por página por solicitud)
        try:
            page_size = int(request.GET.get('page_size', 8))
        except Exception:
            page_size = 8

        def build_page(qs, page_param_name):
            paginator = Paginator(qs, page_size)
            page_number = request.GET.get(page_param_name, 1)
            try:
                page_obj = paginator.page(page_number)
            except (PageNotAnInteger, EmptyPage):
                page_obj = paginator.page(1)
            return page_obj

        active_page_obj = build_page(active_projects, 'active_page')
        completed_page_obj = build_page(completed_projects, 'completed_page')
        
        # Total sin contar archivados
        total_projects = accessible_data['active_count'] + accessible_data['completed_count']
        
        context = {
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_projects': total_projects,
            # Page objects
            'active_page_obj': active_page_obj,
            'completed_page_obj': completed_page_obj,
            'page_size': page_size,
            # Todos los proyectos mostrados son accesibles
            'all_projects_accessible': True,
        }
        return render(request, self.template_name, context)


# ================================
# FINANCE MODULE VIEWS
# ================================

class FinanceDashboardView(LoginRequiredMixin, OrganizationAdminMixin, ProjectPageSizeMixin, ListView):
    """Dashboard principal del módulo financiero con paginación y filtros (solo admin)."""
    model = Project
    template_name = 'projects/finance/dashboard.html'
    context_object_name = 'projects'
    paginate_by = 8
    
    def get_queryset(self):
        """Obtener todos los proyectos de la organización con filtros simples."""
        # OPTIMIZACIÓN: Usar manager optimizado con financial_data
        queryset = Project.objects.with_financial_data().filter(
            organization=self.request.user.organization
        ).exclude(status=Project.Status.ARCHIVED)  # Excluir proyectos archivados
        
        # Filtros
        search = self.request.GET.get('search', '').strip()
        budget_status = self.request.GET.get('budget_status', '')
        
        # Filtro de búsqueda (por nombre de proyecto o cliente)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(client__name__icontains=search)
            )
        
        # Filtro de estado de presupuesto
        if budget_status == 'configured':
            queryset = queryset.filter(budget_configured=True)
        elif budget_status == 'not_configured':
            queryset = queryset.filter(budget_configured=False)
        
        # Ordenar por fecha de creación (más recientes primero)
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = context['projects']
        
        # OPTIMIZACIÓN: Usar caché Redis para estadísticas financieras
        from .finance_cache import get_organization_finance_stats
        
        # Obtener estadísticas desde caché (15 minutos)
        finance_stats = get_organization_finance_stats(
            self.request.user.organization.id
        )
        
        # Parámetros de filtros actuales
        current_filters = {
            'search': self.request.GET.get('search', ''),
            'budget_status': self.request.GET.get('budget_status', ''),
        }
        
        # Construir extra_params para el partial de paginación (preserva filtros)
        params = self.request.GET.copy()
        params.pop('page', None)
        extra_params = params.urlencode()
        if extra_params:
            extra_params = f"{extra_params}&"

        # Usar estadísticas desde caché Redis
        context.update({
            'total_projects': finance_stats['total_projects'],
            'configured_projects': finance_stats['configured_projects'],
            'pending_configuration': finance_stats['pending_configuration'],
            'active_configured': finance_stats['active_configured'],
            'total_budget': finance_stats['total_budget'],
            'total_paid': finance_stats['total_paid'],
            'pending_amount': finance_stats['pending_amount'],
            'overall_percentage': finance_stats['overall_percentage'],
            'current_filters': current_filters,
            'extra_params': extra_params,
        })
        
        return context


class ProjectFinanceDetailView(LoginRequiredMixin, OrganizationAdminMixin, DetailView):
    """Vista detallada de finanzas de un proyecto específico (solo admin)."""
    model = Project
    template_name = 'projects/finance/project_detail.html'
    context_object_name = 'project'
    
    def get_object(self):
        """Obtener proyecto por organización del usuario (sin lógica de accesibles)."""
        project_id = self.kwargs.get('pk')
        # OPTIMIZACIÓN: Prefetch payments para evitar N+1 queries
        return get_object_or_404(
            Project.objects.select_related('client', 'owner').prefetch_related('payments'),
            pk=project_id, 
            organization=self.request.user.organization
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = context['project']
        
        # OPTIMIZACIÓN: Usar caché Redis para estadísticas del proyecto
        from .finance_cache import get_project_finance_stats
        
        # Obtener estadísticas financieras desde caché
        finance_stats = get_project_finance_stats(project.id)
        
        # Pagos recientes (últimos 10) - optimizado con select_related
        recent_payments = project.payments.select_related('created_by').all()[:10]
        
        context.update({
            'recent_payments': recent_payments,
            'payments_count': project.payments.count(),
            'finance_stats': finance_stats,
        })
        
        return context


class ProjectBudgetConfigView(LoginRequiredMixin, OrganizationAdminMixin, UpdateView):
    """Vista para configurar el presupuesto de un proyecto (solo admin)."""
    model = Project
    fields = ['total_budget']
    template_name = 'projects/finance/budget_config.html'
    
    def get_object(self):
        """Verificar acceso al proyecto."""
        from .cache_utils import get_user_accessible_projects
        
        project_id = self.kwargs.get('pk')
        # OPTIMIZACIÓN: Obtener proyectos accesibles con prefetch
        accessible_projects = get_user_accessible_projects(
            self.request.user, 
            self.request.user.organization
        ).prefetch_related('payments')
        
        try:
            return accessible_projects.get(pk=project_id)
        except Project.DoesNotExist:
            raise Http404("Proyecto no encontrado o sin acceso")
    
    def form_valid(self, form):
        """Marcar presupuesto como configurado."""
        form.instance.budget_configured = True
        
        # Manejar caso cuando total_budget es None
        if form.instance.total_budget is not None:
            budget_display = f"${form.instance.total_budget:,.2f}"
            budget_amount = float(form.instance.total_budget)
        else:
            budget_display = "No especificado"
            budget_amount = 0.0
        
        messages.success(
            self.request, 
            f"Presupuesto configurado exitosamente: {budget_display}"
        )
        
        log_project_operation(
            'PROJECT_BUDGET_CONFIGURED',
            self.request.user.email,
            level='INFO',
            project_id=form.instance.pk,
            budget_amount=budget_amount
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy(
            'projects:finance-project-detail', 
            kwargs={'pk': self.object.pk}
        )


class PaymentCreateView(LoginRequiredMixin, OrganizationAdminMixin, CreateView):
    """Vista para registrar un nuevo pago (solo admin)."""
    model = ProjectPayment
    fields = ['amount', 'date', 'description']
    template_name = 'projects/finance/payment_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Cargar el proyecto por organización sin filtros adicionales."""
        self.project_id = kwargs.get('project_id')
        # OPTIMIZACIÓN: Prefetch payments para calcular total_paid sin query adicional
        self.project = get_object_or_404(
            Project.objects.prefetch_related('payments'),
            pk=self.project_id, 
            organization=request.user.organization
        )
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Asignar proyecto y usuario al pago."""
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        # Manejar archivo de comprobante (opcional)
        try:
            uploaded = self.request.FILES.get('receipt')
            if uploaded:
                # Validar extensión permitida
                allowed_exts = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'}
                ext = os.path.splitext(uploaded.name)[1].lower()
                
                # Debug: Log del archivo para diagnóstico
                logger.info(f"Archivo recibido en creación: {uploaded.name}, tamaño: {uploaded.size}, tipo: {uploaded.content_type}, extensión: {ext}")
                
                if ext not in allowed_exts:
                    logger.warning(f"Extensión {ext} no permitida para archivo {uploaded.name}")
                    form.add_error('description', _('Tipo de archivo no permitido. Usa imagen, PDF o Word.'))
                    return super().form_invalid(form)
                
                form.instance.receipt_file = uploaded
        except Exception as e:
            logger.error(f"Error al procesar archivo en creación de pago: {str(e)}", exc_info=True)
            form.add_error('description', f'Error al procesar el archivo: {str(e)}')
            return super().form_invalid(form)
        
        # Validar que no exceda el presupuesto
        if self.project.total_budget:
            new_total = self.project.total_paid + form.instance.amount
            if new_total > self.project.total_budget:
                form.add_error(
                    'amount', 
                    f"Este pago excedería el presupuesto total. "
                    f"Máximo disponible: ${self.project.remaining_amount:,.2f}"
                )
                return super().form_invalid(form)
        
        messages.success(
            self.request, 
            f"Pago registrado exitosamente: ${form.instance.amount:,.2f}"
        )
        
        # OPTIMIZACIÓN: Invalidar caché financiero después de crear pago
        from .finance_cache import invalidate_finance_cache
        invalidate_finance_cache(
            organization_id=self.project.organization.id,
            project_id=self.project.id
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context
    
    def get_success_url(self):
        return reverse_lazy(
            'projects:finance-project-detail', 
            kwargs={'pk': self.project.pk}
        )


class PaymentUpdateView(LoginRequiredMixin, OrganizationAdminMixin, UpdateView):
    """Vista para editar un pago existente (solo admin)."""
    model = ProjectPayment
    fields = ['amount', 'date', 'description']
    template_name = 'projects/finance/payment_form.html'
    
    def get_queryset(self):
        """OPTIMIZACIÓN: Select related del proyecto con payments prefetchados."""
        return super().get_queryset().select_related('project').prefetch_related('project__payments')
    
    def dispatch(self, request, *args, **kwargs):
        """Cargar el proyecto por organización sin filtros adicionales."""
        self.payment = self.get_object()
        self.project = self.payment.project
        
        # Validar organización
        if self.project.organization_id != request.user.organization_id:
            raise Http404("Proyecto no encontrado o sin acceso")
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Validar que no exceda el presupuesto."""
        # Calcular el monto que se restaría del total actual
        old_amount = self.object.amount
        new_amount = form.instance.amount
        difference = new_amount - old_amount
        # Guardar referencia del archivo anterior para limpieza post-guardado
        old_receipt_name = self.object.receipt_file.name if getattr(self.object, 'receipt_file', None) else None
        
        if self.project.total_budget:
            new_total = self.project.total_paid + difference
            if new_total > self.project.total_budget:
                form.add_error(
                    'amount', 
                    f"Este cambio excedería el presupuesto total. "
                    f"Máximo disponible: ${self.project.remaining_amount + old_amount:,.2f}"
                )
                return super().form_invalid(form)
        
        # Manejar reemplazo de comprobante si se sube uno nuevo
        try:
            uploaded = self.request.FILES.get('receipt')
            if uploaded:
                allowed_exts = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'}
                ext = os.path.splitext(uploaded.name)[1].lower()
                
                # Debug: Log del archivo para diagnóstico
                logger.info(f"Archivo recibido en edición: {uploaded.name}, tamaño: {uploaded.size}, tipo: {uploaded.content_type}, extensión: {ext}")
                
                if ext not in allowed_exts:
                    logger.warning(f"Extensión {ext} no permitida para archivo {uploaded.name}")
                    form.add_error('description', _('Tipo de archivo no permitido. Usa imagen, PDF o Word.'))
                    return super().form_invalid(form)
                
                form.instance.receipt_file = uploaded  # Reemplaza referencia al archivo
        except Exception as e:
            logger.error(f"Error al procesar archivo en edición de pago: {str(e)}", exc_info=True)
            form.add_error('description', f'Error al procesar el archivo: {str(e)}')
            return super().form_invalid(form)

        # Guardar cambios primero y luego eliminar el archivo anterior de forma segura
        response = super().form_valid(form)

        try:
            if uploaded and old_receipt_name and default_storage.exists(old_receipt_name):
                default_storage.delete(old_receipt_name)
        except Exception:
            # No bloquear el flujo si falla la eliminación; se puede limpiar con tareas programadas
            pass

        messages.success(
            self.request, 
            f"Pago actualizado exitosamente: ${form.instance.amount:,.2f}"
        )
        
        # OPTIMIZACIÓN: Invalidar caché financiero después de actualizar pago
        from .finance_cache import invalidate_finance_cache
        invalidate_finance_cache(
            organization_id=self.project.organization.id,
            project_id=self.project.id
        )

        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['is_edit'] = True
        return context
    
    def get_success_url(self):
        return reverse_lazy(
            'projects:finance-project-detail', 
            kwargs={'pk': self.project.pk}
        )


class PaymentDeleteView(LoginRequiredMixin, OrganizationAdminMixin, DeleteView):
    """Eliminar un pago y su comprobante asociado del storage (solo admin)."""
    model = ProjectPayment
    template_name = 'projects/finance/payment_confirm_delete.html'
    context_object_name = 'payment'

    def dispatch(self, request, *args, **kwargs):
        self.payment = self.get_object()
        self.project = self.payment.project
        if self.project.organization_id != request.user.organization_id:
            raise Http404("Pago no encontrado o sin acceso")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        old_receipt_name = self.payment.receipt_file.name if getattr(self.payment, 'receipt_file', None) else None
        response = super().delete(request, *args, **kwargs)
        try:
            if old_receipt_name and default_storage.exists(old_receipt_name):
                default_storage.delete(old_receipt_name)
        except Exception:
            pass
        messages.success(request, 'Pago eliminado correctamente')
        return response

    def get_success_url(self):
        return reverse_lazy('projects:finance-project-detail', kwargs={'pk': self.project.pk})

    def get(self, request, *args, **kwargs):
        # No mostramos plantilla de confirmación; flujo simple y directo
        return redirect(self.get_success_url())


class ProjectToggleStatusView(LoginRequiredMixin, View):
    """Vista AJAX para cambiar el estado ACTIVE/ARCHIVED de un proyecto (solo admin)"""
    
    def dispatch(self, request, *args, **kwargs):
        project_to_toggle = get_object_or_404(Project, pk=kwargs['pk'])
        current_user = request.user
        
        # Solo org_admin puede cambiar estado de proyectos de su organización
        if not (current_user.is_org_admin and current_user.organization and 
                project_to_toggle.organization == current_user.organization):
            raise PermissionDenied("No tienes permisos para modificar este proyecto")
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        """Cambiar estado del proyecto entre ACTIVE y ARCHIVED"""
        project_to_toggle = get_object_or_404(Project, pk=pk)
        
        try:
            data = json.loads(request.body)
            # En vez de is_active, recibimos el nuevo estado deseado
            # Si is_active=true => ACTIVE, si false => ARCHIVED
            is_active = data.get('is_active', False)
            new_status = Project.Status.ACTIVE if is_active else Project.Status.ARCHIVED
            
            # Cambiar estado
            old_status = project_to_toggle.status
            project_to_toggle.status = new_status
            project_to_toggle.save()
            
            # Invalidar cache después de cambiar estado
            from .cache_utils import invalidate_project_cache, invalidate_kanban_projects_cache
            invalidate_project_cache(project_to_toggle.organization.id, project_to_toggle.id)
            invalidate_kanban_projects_cache(project_to_toggle.organization.id)
            
            # Log del cambio
            action = "activado" if is_active else "archivado"
            logger.info(
                f"Proyecto {action}: {project_to_toggle.name} "
                f"(ID: {project_to_toggle.id}, de {old_status} a {new_status}, por {request.user.email})"
            )
            
            # Obtener estadísticas actualizadas para proyectos
            org = request.user.organization
            total_projects = Project.objects.filter(organization=org).count()
            active_projects = Project.objects.filter(organization=org, status=Project.Status.ACTIVE).count()
            archived_projects = Project.objects.filter(organization=org, status=Project.Status.ARCHIVED).count()
            completed_projects = Project.objects.filter(organization=org, status=Project.Status.COMPLETED).count()
            
            return JsonResponse({
                'success': True,
                'message': f"Proyecto {action} correctamente",
                'new_status': is_active,
                'stats': {
                    'total_projects': total_projects,
                    'active_projects': active_projects,
                    'archived_projects': archived_projects,
                    'completed_projects': completed_projects
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos'
            }, status=400)
        except Exception as e:
            logger.error(f"Error al cambiar estado de proyecto: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Error al cambiar el estado del proyecto'
            }, status=500)