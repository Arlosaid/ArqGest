from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView
)
from .models import Project, Task, Phase, ProjectTemplate
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import TaskForm, ProjectForm


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, phase__project__owner=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('projects:project-detail', pk=task.phase.project.pk)
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'projects/partials/task_edit_modal.html', {'form': form, 'task': task})


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        """
        Ensure users can only see projects from their organization.
        """
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Project.objects.filter(owner__organization=self.request.user.organization).order_by('-created_at')
        return Project.objects.none()

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_form_kwargs(self):
        """
        Pass the organization to the form.
        """
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'organization'):
            kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        """
        Assign the current user as the owner and create phases from a template if selected.
        If no template is chosen, create default phases.
        """
        form.instance.owner = self.request.user
        form.instance.organization = self.request.user.organization
        
        response = super().form_valid(form)

        template = form.cleaned_data.get('template')
        if template:
            phase_templates = template.phase_templates.all().order_by('order')
            for phase_template in phase_templates:
                Phase.objects.create(
                    project=self.object,
                    name=phase_template.name,
                    order=phase_template.order
                )
        else:
            default_phases = [
                _("Por Hacer"), 
                _("En Progreso"), 
                _("Revisión"), 
                _("Bloqueado"), 
                _("Completado")
            ]
            for i, phase_name in enumerate(default_phases):
                Phase.objects.create(
                    project=self.object,
                    name=str(phase_name),
                    order=i
                )
        
        return response

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        phases = project.phases.order_by('order').prefetch_related('tasks')
        context['phases'] = phases
        if 'task_form' not in context:
            context['task_form'] = TaskForm(user=self.request.user)
            
        return context

    def test_func(self):
        project = self.get_object()
        return self.request.user.organization == project.owner.organization

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_form_kwargs(self):
        """
        Pass the organization to the form.
        """
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'organization'):
            kwargs['organization'] = self.request.user.organization
        return kwargs

    def test_func(self):
        project = self.get_object()
        return self.request.user.organization == project.owner.organization

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        project = self.get_object()
        return self.request.user.organization == project.owner.organization

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        """
        Users can only see tasks from projects within their organization.
        """
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Task.objects.filter(phase__project__owner__organization=self.request.user.organization).order_by('status', '-created_at')
        return Task.objects.none()


@login_required
@require_POST
def advance_project_phase(request, pk):
    """
    Advances the project to the next phase.
    """
    project = get_object_or_404(Project, pk=pk, owner__organization=request.user.organization)
    
    current_phase_index = project.Phases.values.index(project.phase)
    
    if current_phase_index < len(project.Phases.values) - 1:
        next_phase = project.Phases.values[current_phase_index + 1]
        project.phase = next_phase
        project.save()
        messages.success(request, _(f"Project advanced to {project.get_phase_display()}"))
    else:
        messages.info(request, _("The project is already in the final phase."))
        
    return redirect('projects:project-detail', pk=project.pk)

@login_required
@require_POST
def update_task_status(request, task_pk):
    """
    Updates the status of a task.
    """
    task = get_object_or_404(Task, pk=task_pk, phase__project__owner__organization=request.user.organization)
    new_status = request.POST.get('status')

    if new_status in Task.Status.values:
        task.status = new_status
        task.save()
        messages.success(request, _("Task status updated successfully."))
    else:
        messages.error(request, _("Invalid status provided."))

    return redirect(request.META.get('HTTP_REFERER', reverse_lazy('projects:task-list')))


@login_required
@require_POST
def task_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, owner__organization=request.user.organization)
    
    phase_id = request.POST.get('phase')
    if not phase_id:
        messages.error(request, _("Could not determine the phase for the new task."))
        return redirect('projects:project-detail', pk=project.pk)

    phase = get_object_or_404(Phase, id=phase_id, project=project)
    
    # Quick-add form only submits a title.
    # We check for other fields to decide if it's the full form.
    is_quick_add = 'description' not in request.POST and 'priority' not in request.POST

    if is_quick_add:
        data = {
            'title': request.POST.get('title'),
            'description': '',
            'priority': Task.Priority.MEDIUM,
            'status': Task.Status.TODO,
        }
        form = TaskForm(data, user=request.user)
    else:
        form = TaskForm(request.POST, user=request.user)

    if form.is_valid():
        task = form.save(commit=False)
        task.phase = phase
        task.save()
        messages.success(request, _("Task created successfully."))
        
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse_lazy('projects:project-detail', kwargs={'pk': project.pk})
        return response
    else:
        messages.error(request, _("There was an error creating the task. Please check the data."))
        
        phases = project.phases.order_by('order').prefetch_related('tasks')
        context = {
            'project': project,
            'phases': phases,
            'task_form': form,
            'error_phase_id': phase.id
        }
        return render(request, 'projects/project_detail.html', context)

@login_required
@require_POST
def move_task(request, task_pk):
    """
    Handles moving a task to a new phase via HTMX.
    """
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__owner__organization=request.user.organization)
        
        new_phase_id = request.POST.get('phase_id')
        if not new_phase_id:
            return HttpResponseBadRequest("Phase ID is missing.")

        new_phase = get_object_or_404(Phase, pk=new_phase_id, project__owner__organization=request.user.organization)

        task.phase = new_phase
        task.save(update_fields=['phase'])

        return HttpResponse(status=200)

    except Exception as e:
        print(f"Error moving task: {e}")
        return HttpResponseBadRequest("An error occurred while moving the task.")

class MyTaskListView(LoginRequiredMixin, ListView):
    """
    Displays a list of tasks assigned to the current user across all projects.
    """
    model = Task
    template_name = 'projects/my_tasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        """
        Returns tasks assigned to the currently logged-in user,
        ordered by due date.
        """
        return Task.objects.filter(
            assigned_to=self.request.user
        ).order_by('due_date')

    def get_context_data(self, **kwargs):
        """
        Adds the total count of tasks to the context.
        """
        context = super().get_context_data(**kwargs)
        context['total_tasks'] = self.get_queryset().count()
        return context
