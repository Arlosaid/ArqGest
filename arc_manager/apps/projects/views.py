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
from .models import Project, Task, Phase, PhaseTemplate
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
            org_id = self.request.user.organization.id
            logger.info(f"Fetching projects for organization {org_id} - User: {self.request.user.email}")
            return Project.objects.filter(
                organization=self.request.user.organization
            ).select_related('client', 'owner').order_by('-created_at')
        logger.warning(f"User {self.request.user.email} accessed project list without organization")
        return Project.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            org_id = self.request.user.organization.id
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
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            org_id = self.request.user.organization.id
            logger.debug(f"Filtering project detail for organization {org_id}")
            return super().get_queryset().filter(organization=self.request.user.organization)
        logger.warning(f"User {self.request.user.email} attempted to access project detail without organization")
        return super().get_queryset().none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
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

class ProjectCreateView(LoginRequiredMixin, CreateView):
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
        
        project_name = form.cleaned_data.get('name')
        org_id = self.request.user.organization.id if self.request.user.organization else 'None'
        
        logger.info(f"Starting project creation - Name: '{project_name}', Org: {org_id}, User: {self.request.user.email}, Method: {creation_method}")

        if creation_method == 'manual' and not phase_formset.is_valid():
            logger.warning(f"Project creation failed - Invalid phase formset for project '{project_name}'")
            return self.form_invalid(form)

        form.instance.owner = self.request.user
        form.instance.organization = self.request.user.organization
        
        try:
            self.object = form.save()
            logger.info(f"Project created successfully - ID: {self.object.id}, Name: '{project_name}', Owner: {self.request.user.email}")
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
            logger.info(f"Phases created for project {self.object.id} using method: {creation_method}")
        except Exception as e:
            logger.error(f"Phase creation failed for project {self.object.id}: {str(e)}", exc_info=True)

        return redirect(self.get_success_url())

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)

    def form_valid(self, form):
        project_name = form.cleaned_data.get('name')
        project_id = self.object.id
        logger.info(f"Updating project {project_id} - New name: '{project_name}', User: {self.request.user.email}")
        
        try:
            result = super().form_valid(form)
            logger.info(f"Project {project_id} updated successfully")
            return result
        except IntegrityError as e:
            logger.error(f"Project update failed for {project_id} - IntegrityError: {str(e)}")
            form.add_error('name', _('Ya existe un proyecto con este nombre en tu organización.'))
            return self.form_invalid(form)

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
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
        
        logger.warning(f"Deleting project {project_id} - Name: '{project_name}', Org: {org_id}, User: {request.user.email}")
        
        try:
            result = super().delete(request, *args, **kwargs)
            logger.info(f"Project {project_id} ('{project_name}') deleted successfully")
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
    project = get_object_or_404(Project, pk=pk, organization=request.user.organization)
    
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
    
    logger.debug(f"Task creation request for project {project_pk} by user {request.user.email}")
    
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
                
                log_msg, log_data = log_task_operation(
                    'CREATE_TASK',
                    request.user.email,
                    project_id=project_pk,
                    phase_id=phase_id,
                    title=title,
                    priority=priority
                )
                logger.info(log_msg)
                
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
                        
                        log_msg, log_data = log_task_operation(
                            'ASSIGN_TASK',
                            request.user.email,
                            task_id=task.id,
                            assignee_id=assigned_to_id
                        )
                        logger.info(log_msg)
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
                
                log_msg, log_data = log_task_operation(
                    'CREATE_TASK_SUCCESS',
                    request.user.email,
                    task_id=task.id,
                    project_id=project_pk,
                    title=title
                )
                logger.info(log_msg)

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
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')
        
        query_time = time.time() - start_time
        task_count = queryset.count()
        
        log_msg, log_data = log_task_operation(
            'LIST_ALL_TASKS',
            self.request.user.email,
            org_id=self.request.user.organization.id,
            task_count=task_count,
            query_time_ms=round(query_time * 1000, 2)
        )
        
        if query_time > 2.0:  # Log slow queries
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_QUERY_SLOW}")
        elif task_count > 1000:  # Log large datasets
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_LIST_LARGE_DATASET}")
        else:
            logger.info(log_msg)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_tasks = Task.objects.filter(phase__project__organization=self.request.user.organization)
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
        
        log_msg, log_data = log_task_operation(
            'LIST_MY_TASKS',
            self.request.user.email,
            org_id=self.request.user.organization.id,
            task_count=task_count,
            query_time_ms=round(query_time * 1000, 2),
            filters={'status': status_filter, 'priority': priority_filter, 'search': search_filter}
        )
        
        if query_time > 2.0:
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_QUERY_SLOW}")
        else:
            logger.info(log_msg)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todas las tareas del usuario sin filtros
        all_tasks = Task.objects.filter(
            phase__project__organization=self.request.user.organization,
            assigned_to=self.request.user
        )
        
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
            
            log_msg, log_data = log_task_operation(
                'UPDATE_TASK_STATUS',
                request.user.email,
                task_id=task_pk,
                old_status=old_status,
                new_status=status
            )
            logger.info(log_msg)
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
                
                log_msg, log_data = log_task_operation(
                    'MOVE_TASK',
                    request.user.email,
                    task_id=task_pk,
                    old_phase_id=old_phase_id,
                    old_phase_name=old_phase_name,
                    new_phase_id=phase_id,
                    new_phase_name=new_phase.name
                )
                logger.info(log_msg)
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
        
        log_msg, log_data = log_task_operation(
            'ACCESS_TASK_EDIT',
            request.user.email,
            task_id=pk,
            method=request.method
        )
        logger.info(log_msg)

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
        try:
            form = TaskForm(request.POST, instance=task, project=project)
        except Exception as e:
            log_msg, log_data = log_task_operation(
                'FORM_INIT_ERROR',
                request.user.email,
                task_id=pk,
                error_code=TaskErrorCodes.TASK_UPDATE_FORM_VALIDATION,
                exception=str(e)
            )
            logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_FORM_VALIDATION}", exc_info=True)
            
            if request.headers.get('HX-Request'):
                return HttpResponse(f"Error al inicializar formulario: {e}", status=500)
            messages.error(request, _('Error al procesar el formulario.'))
            return redirect('projects:project-detail', pk=project.id)
        
        if form.is_valid():
            try:
                task = form.save()
                
                log_msg, log_data = log_task_operation(
                    'EDIT_TASK_SUCCESS',
                    request.user.email,
                    task_id=pk,
                    title=task.title
                )
                logger.info(log_msg)

                if request.headers.get('HX-Request'):
                    # Para HTMX, devolver un mensaje de éxito que active el cierre del modal
                    return HttpResponse(
                        '<div class="alert alert-success">Tarea actualizada correctamente</div>',
                        status=200
                    )
                else:
                    # Para peticiones normales, redirigir al kanban del proyecto
                    messages.success(request, _('Tarea actualizada correctamente.'))
                    return redirect('projects:project-kanban', pk=project.id)

            except Exception as e:
                log_msg, log_data = log_task_operation(
                    'EDIT_TASK_ERROR',
                    request.user.email,
                    task_id=pk,
                    error_code=TaskErrorCodes.TASK_UPDATE_SAVE_ERROR,
                    exception=str(e)
                )
                logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_SAVE_ERROR}", exc_info=True)
                
                if request.headers.get('HX-Request'):
                    return HttpResponse(f"Error al guardar: {e}", status=400)
                messages.error(request, _('Error al guardar la tarea. Inténtalo de nuevo.'))
                return redirect('projects:project-detail', pk=project.id)
        else:
            # Si el formulario no es válido, registrar errores y devolverlos
            error_details = form.errors.as_json()
            
            log_msg, log_data = log_task_operation(
                'EDIT_TASK_ERROR',
                request.user.email,
                task_id=pk,
                error_code=TaskErrorCodes.TASK_UPDATE_FORM_VALIDATION,
                form_errors=error_details
            )
            logger.warning(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_FORM_VALIDATION}")
            # Para HTMX, devolvemos el formulario con errores para mostrar en el modal
            if request.headers.get('HX-Request'):
                # Re-renderizar el modal con el formulario y sus errores
                context = {
                    'task': task,
                    'form': form, # Pasar el formulario con errores al contexto
                    'project': project,
                    'project_color': get_project_color(project.id),
                    'phases': project.phases.all(),
                    'users': project.organization.users.filter(is_active=True, is_superuser=False),
                    'priority_choices': Task.Priority.choices,
                }
                return render(request, 'projects/partials/task_edit_modal.html', context)

            # Para peticiones normales, mostrar mensaje de error
            error_message = _('Por favor, corrige los errores a continuación.')
            # Unir los errores en un solo string para el mensaje
            error_list = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
            messages.error(request, f"{error_message} {' | '.join(error_list)}")


    # Para GET, mostrar formulario de edición
    try:
        form = TaskForm(instance=task, project=project)
    except Exception as e:
        log_msg, log_data = log_task_operation(
            'FORM_INIT_ERROR',
            request.user.email,
            task_id=pk,
            error_code=TaskErrorCodes.TASK_UPDATE_FORM_VALIDATION,
            exception=str(e)
        )
        logger.error(f"{log_msg} ERROR_CODE: {TaskErrorCodes.TASK_UPDATE_FORM_VALIDATION}", exc_info=True)
        
        if request.headers.get('HX-Request'):
            return HttpResponse(f"Error al cargar formulario: {e}", status=500)
        messages.error(request, _('Error al cargar el formulario de edición.'))
        return redirect('projects:project-detail', pk=project.id)

    context = {
        'task': task,
        'form': form,
        'project': project,
        'project_color': get_project_color(project.id),
        'phases': project.phases.all(),
        'users': project.organization.users.filter(is_active=True, is_superuser=False),
        'priority_choices': Task.Priority.choices,
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
    
    log_msg, log_data = log_task_operation(
        'DELETE_TASK_ATTEMPT',
        request.user.email,
        task_id=pk,
        title=task_title,
        project_id=project_id
    )
    logger.warning(log_msg)
    
    try:
        task.delete()
        
        log_msg, log_data = log_task_operation(
            'DELETE_TASK_SUCCESS',
            request.user.email,
            task_id=pk,
            title=task_title,
            project_id=project_id
        )
        logger.info(log_msg)
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
    
    log_msg, log_data = log_task_operation(
        'VIEW_PAGINATED_TASKS',
        request.user.email,
        project_id=project_pk,
        page=page,
        per_page=per_page,
        phase_filter=phase_filter
    )
    logger.info(log_msg)

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
class PhaseTemplateListView(LoginRequiredMixin, ProjectPageSizeMixin, ListView):
    paginate_by = 8
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        # Mostrar solo plantillas de la organización del usuario para gestión
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return PhaseTemplate.objects.filter(organization=self.request.user.organization)
        return PhaseTemplate.objects.none()

class PhaseTemplateCreateView(LoginRequiredMixin, CreateView):
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

class PhaseTemplateDetailView(LoginRequiredMixin, DetailView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        # Limitar la vista de detalle a plantillas de la organización
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return PhaseTemplate.objects.filter(organization=self.request.user.organization)
        return PhaseTemplate.objects.none()

class PhaseTemplateUpdateView(LoginRequiredMixin, UpdateView):
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

class PhaseTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_confirm_delete.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)


@login_required
def task_detail(request, pk):
    """Vista para mostrar los detalles de una tarea en formato modal"""
    log_msg, log_data = log_task_operation(
        'VIEW_TASK_DETAILS',
        request.user.email,
        task_id=pk
    )
    logger.info(log_msg)
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
        # Obtener proyectos del usuario
        if request.user.is_org_admin:
            projects = Project.objects.filter(organization=request.user.organization)
        else:
            # Filtrar proyectos donde el usuario tenga tareas asignadas
            projects = (
                Project.objects
                .filter(
                    organization=request.user.organization,
                    phases__tasks__assigned_to=request.user,
                )
                .distinct()
            )
        
        # Agrupar por estado - CORREGIDO para usar los estados reales del modelo
        active_projects = projects.filter(status='ACTIVE')
        completed_projects = projects.filter(status='COMPLETED')
        archived_projects = projects.filter(status='ARCHIVED')

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
        archived_page_obj = build_page(archived_projects, 'archived_page')
        
        context = {
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'archived_projects': archived_projects,  # Colecciones completas para contadores
            'total_projects': projects.count(),
            # Page objects
            'active_page_obj': active_page_obj,
            'completed_page_obj': completed_page_obj,
            'archived_page_obj': archived_page_obj,
            'page_size': page_size,
        }
        return render(request, self.template_name, context)
