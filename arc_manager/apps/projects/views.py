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
from .models import Project, Task, Phase, PhaseTemplate
from apps.files.models import ProjectFile
from .forms import ProjectForm, TaskForm, PhaseTemplateForm, PhaseFormSet
from .services import create_phases_for_project  # Importar el nuevo servicio
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from datetime import datetime
import json
from django.utils import timezone
from core.mixins import PageSizeMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Project Views
class ProjectListView(LoginRequiredMixin, PageSizeMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 6

    def get_queryset(self):
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Project.objects.filter(
                organization=self.request.user.organization
            ).select_related('client', 'owner').order_by('-created_at')
        return Project.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            projects_all = Project.objects.filter(organization=self.request.user.organization)
            # Contadores por estado básicos
            context['total_projects'] = projects_all.count()
            try:
                context['active_projects_count'] = projects_all.filter(status='ACTIVE').count()
                context['completed_projects_count'] = projects_all.filter(status='COMPLETED').count()
                context['archived_projects_count'] = projects_all.filter(status='ARCHIVED').count()
            except Exception:
                # Si el modelo no tiene estos estados, degradar con cero
                context.setdefault('active_projects_count', 0)
                context.setdefault('completed_projects_count', 0)
                context.setdefault('archived_projects_count', 0)
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Obtener fases del proyecto con sus archivos y tareas (optimizado)
        phases = project.phases.prefetch_related(
            'files', 'files__uploaded_by',
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

        # Paginación: pestaña Fases (6 por página)
        phases_page_obj = build_page(phases, 6, 'phases_page')
        context['phases_page_obj'] = phases_page_obj

        # Paginación: pestaña Archivos → listado de fases (4 por página)
        files_phases_page_obj = build_page(phases, 4, 'files_phases_page')
        context['files_phases_page_obj'] = files_phases_page_obj

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

        # Centro de tareas (pestaña interna): paginar 10 por página
        tasks_page_obj = build_page(tasks_qs.order_by('due_date', 'priority'), 10, 'tasks_page')
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

        # Paginación de archivos por fase dentro de la pestaña Archivos (5 por página por fase mostrada)
        for phase in getattr(files_phases_page_obj, 'object_list', []):
            files_qs = getattr(phase, 'files').all()
            setattr(phase, 'files_page_obj', build_page(files_qs, 5, f'file_page_{phase.id}'))
        
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

        if creation_method == 'manual' and not phase_formset.is_valid():
            return self.form_invalid(form)

        form.instance.owner = self.request.user
        form.instance.organization = self.request.user.organization
        
        try:
            self.object = form.save()
        except IntegrityError:
            # Nombre duplicado u otra restricción a nivel BD
            form.add_error('name', _('Ya existe un proyecto con este nombre en tu organización.'))
            return self.form_invalid(form)

        create_phases_for_project(
            project=self.object,
            creation_method=creation_method,
            phase_template=form.cleaned_data.get('phase_template'),
            phase_formset=phase_formset
        )

        return redirect(self.get_success_url())

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('name', _('Ya existe un proyecto con este nombre en tu organización.'))
            return self.form_invalid(form)

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project-list')

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)

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
            tasks_by_status[code] = [t for t in tasks_list if t.status == code]

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
                        error_msg = _('El usuario seleccionado no pertenece a tu organización.')
                        messages.error(request, error_msg)
                        accepts_json = 'application/json' in request.headers.get('Accept', '')
                        is_htmx = request.headers.get('HX-Request')
                        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                        if accepts_json or is_htmx or is_ajax:
                            return JsonResponse({'success': False, 'error': 'invalid_assignee'}, status=400)
                
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
                messages.error(request, 'La fase seleccionada no existe.')
        else:
            messages.error(request, 'El título y la fase son requeridos.')
    
    return redirect('projects:project-detail', pk=project_pk)

class TaskListView(LoginRequiredMixin, PageSizeMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(
            phase__project__organization=self.request.user.organization
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')

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

class MyTaskListView(LoginRequiredMixin, PageSizeMixin, ListView):
    model = Task
    template_name = 'projects/my_tasks.html'
    context_object_name = 'tasks'
    paginate_by = 8

    def get_queryset(self):
        return Task.objects.filter(
            phase__project__organization=self.request.user.organization,
            assigned_to=self.request.user
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_tasks = Task.objects.filter(
            phase__project__organization=self.request.user.organization,
            assigned_to=self.request.user
        )
        context['total_tasks'] = all_tasks.count()
        context['tasks_todo'] = all_tasks.filter(status='TODO').count()
        context['tasks_in_progress'] = all_tasks.filter(status='IN_PROGRESS').count()
        context['tasks_paused'] = all_tasks.filter(status='PAUSED').count()
        context['tasks_done'] = all_tasks.filter(status='DONE').count()
        context['today'] = timezone.now().date()
        return context

@login_required
@require_POST
def update_task_status(request, task_pk):
    """Actualizar el estado de una tarea."""
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__organization=request.user.organization)
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
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.error('update_task_status failed', exc_info=True)
        return JsonResponse({'success': False, 'error': 'Unexpected error'})

@login_required
@require_POST
def move_task(request, task_pk):
    """Mover una tarea a otra fase."""
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__organization=request.user.organization)
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
                return JsonResponse({'success': False, 'error': 'Fase no encontrada'})
        else:
            return JsonResponse({'success': False, 'error': 'ID de fase requerido'})
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.error('move_task failed', exc_info=True)
        return JsonResponse({'success': False, 'error': 'Unexpected error'})

@login_required
def task_edit(request, pk):
    """Editar una tarea."""
    task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        status = request.POST.get('status') or task.status
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        assigned_to_id = request.POST.get('assigned_to')
        phase_id = request.POST.get('phase')
        
        if title:
            task.title = title
            task.description = description
            task.status = status
            task.priority = priority
            task.due_date = due_date if due_date else None
            if assigned_to_id:
                eligible_qs = task.phase.project.organization.users.filter(
                    pk=assigned_to_id,
                    is_active=True,
                    is_superuser=False
                )
                if eligible_qs.exists():
                    task.assigned_to_id = assigned_to_id
                else:
                    task.assigned_to = None
            if phase_id and str(task.phase_id) != str(phase_id):
                try:
                    task.phase = Phase.objects.get(pk=phase_id, project=task.phase.project)
                except Phase.DoesNotExist:
                    pass
            task.save()
            
            # Respuesta para htmx: devolver JSON para actualizar la tarjeta y cerrar modal
            # Solo mostrar mensaje Django para peticiones normales (no AJAX)
            if request.headers.get('HX-Request'):
                assigned_name = ''
                if task.assigned_to:
                    assigned_name = task.assigned_to.get_full_name() or task.assigned_to.username or str(task.assigned_to)
                payload = {
                    'success': True,
                    'task': {
                        'id': task.id,
                        'title': task.title,
                        'assigned_to_name': assigned_name,
                        'phase_name': task.phase.name,
                    }
                }
                return JsonResponse(payload)
            else:
                return redirect('projects:project-detail', pk=task.phase.project.pk)
        else:
            messages.error(request, 'El título es requerido.')
    
    # Para GET, mostrar formulario de edición
    context = {
        'task': task,
        'project': task.phase.project,
        'phases': task.phase.project.phases.all(),
        'users': (
            task.phase.project.organization.users.filter(is_active=True, is_superuser=False).exclude(is_org_admin=True)
            if hasattr(task.phase.project.organization, 'users') else []
        ),
        'status_choices': Task.Status.choices,
        'priority_choices': Task.Priority.choices,
    }
    
    return render(request, 'projects/partials/task_edit_modal.html', context)

@login_required
@require_POST
def task_delete(request, pk):
    """Eliminar una tarea (JSON)."""
    task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
    task.delete()
    return JsonResponse({'success': True})

# PhaseTemplate Views
class PhaseTemplateListView(LoginRequiredMixin, PageSizeMixin, ListView):
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
    task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
    
    context = {
        'task': task,
        'project': task.phase.project,
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
