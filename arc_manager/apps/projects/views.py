from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Project, Task, Phase, PhaseTemplate
from .forms import ProjectForm, TaskForm, PhaseTemplateForm, PhaseFormSet
from .services import create_phases_for_project  # Importar el nuevo servicio

# Project Views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Project.objects.filter(
                organization=self.request.user.organization
            ).select_related('client', 'owner').order_by('-created_at')
        return Project.objects.none()

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.user.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Obtener fases del proyecto con sus tareas
        phases = project.phases.prefetch_related('tasks__assigned_to').order_by('order')
        
        # Obtener todas las tareas del proyecto
        tasks = Task.objects.filter(phase__project=project).select_related('phase', 'assigned_to').order_by('due_date', 'priority')
        
        from datetime import date
        context['phases'] = phases
        context['tasks'] = tasks
        context['today'] = date.today()
        
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
        
        self.object = form.save()

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
    
    # Obtener fases con sus tareas
    phases = project.phases.prefetch_related('tasks__assigned_to').order_by('order')
    
    # Obtener estadísticas de tareas
    all_tasks = Task.objects.filter(phase__project=project)
    tasks_done = all_tasks.filter(status='DONE').count()
    tasks_in_progress = all_tasks.filter(status='IN_PROGRESS').count()
    tasks_paused = all_tasks.filter(status='PAUSED').count()
    
    context = {
        'project': project,
        'phases': phases,
        'tasks_done': tasks_done,
        'tasks_in_progress': tasks_in_progress,
        'tasks_paused': tasks_paused,
    }
    
    return render(request, 'projects/kanban_board.html', context)

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
        due_date = request.POST.get('due_date')
        
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
                
                if assigned_to_id:
                    task.assigned_to_id = assigned_to_id
                    task.save()
                
                messages.success(request, f'Tarea "{title}" creada exitosamente.')
                
                # Redirigir según el origen
                if request.headers.get('HX-Request'):
                    return HttpResponse('Tarea creada exitosamente')
                else:
                    # Si viene del kanban, redirigir al kanban
                    if 'kanban' in request.META.get('HTTP_REFERER', ''):
                        return redirect('projects:project-kanban', pk=project_pk)
                    else:
                        return redirect('projects:project-detail', pk=project_pk)
                    
            except Phase.DoesNotExist:
                messages.error(request, 'La fase seleccionada no existe.')
        else:
            messages.error(request, 'El título y la fase son requeridos.')
    
    return redirect('projects:project-detail', pk=project_pk)

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(
            phase__project__organization=self.request.user.organization
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')

class MyTaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/my_tasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(
            phase__project__organization=self.request.user.organization,
            assigned_to=self.request.user
        ).select_related('phase__project', 'assigned_to').order_by('due_date', 'priority')

@login_required
@require_POST
def update_task_status(request, task_pk):
    """Actualizar el estado de una tarea."""
    from django.http import JsonResponse
    
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__organization=request.user.organization)
        status = request.POST.get('status')
        
        if status in dict(Task.Status.choices):
            task.status = status
            task.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def move_task(request, task_pk):
    """Mover una tarea a otra fase."""
    from django.http import JsonResponse
    
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__organization=request.user.organization)
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
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def task_edit(request, pk):
    """Editar una tarea."""
    task = get_object_or_404(Task, pk=pk, phase__project__organization=request.user.organization)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        assigned_to_id = request.POST.get('assigned_to')
        
        if title:
            task.title = title
            task.description = description
            task.status = status
            task.priority = priority
            task.due_date = due_date if due_date else None
            task.assigned_to_id = assigned_to_id if assigned_to_id else None
            task.save()
            
            messages.success(request, f'Tarea "{title}" actualizada exitosamente.')
            
            # Redirigir según el origen
            if request.headers.get('HX-Request'):
                return HttpResponse('Tarea actualizada exitosamente')
            else:
                return redirect('projects:project-detail', pk=task.phase.project.pk)
        else:
            messages.error(request, 'El título es requerido.')
    
    # Para GET, mostrar formulario de edición
    context = {
        'task': task,
        'project': task.phase.project,
        'phases': task.phase.project.phases.all(),
        'status_choices': Task.Status.choices,
        'priority_choices': Task.Priority.choices,
    }
    
    return render(request, 'projects/partials/task_edit_modal.html', context)

# PhaseTemplate Views
class PhaseTemplateListView(LoginRequiredMixin, ListView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_list.html'
    context_object_name = 'templates'

class PhaseTemplateCreateView(LoginRequiredMixin, CreateView):
    model = PhaseTemplate
    form_class = PhaseTemplateForm
    template_name = 'projects/phasetemplate_form.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

class PhaseTemplateDetailView(LoginRequiredMixin, DetailView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_detail.html'
    context_object_name = 'template'

class PhaseTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = PhaseTemplate
    form_class = PhaseTemplateForm
    template_name = 'projects/phasetemplate_form.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

class PhaseTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_confirm_delete.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

# Force reload
