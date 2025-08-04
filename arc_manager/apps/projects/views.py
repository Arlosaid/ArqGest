from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView
)
from .models import Project, Task
from .forms import TaskForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        """
        Ensure users can only see their own projects.
        """
        return Project.objects.filter(owner=self.request.user).order_by('-created_at')

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'client']
    success_url = reverse_lazy('projects:project-list')

    def form_valid(self, form):
        """
        Assign the current user as the owner of the new project.
        """
        form.instance.owner = self.request.user
        return super().form_valid(form)

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Obtener todas las fases del proyecto, ordenadas, y precargar las tareas
        # para evitar consultas adicionales a la base de datos en el bucle.
        phases = project.phases.order_by('order').prefetch_related('tasks')

        context['phases'] = phases
        context['task_form'] = TaskForm()
        return context

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.owner

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'client']
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.owner

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.owner

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        """
        Users can only see tasks from projects they own.
        """
        # Order by status (e.g., pending first), then by creation date
        return Task.objects.filter(phase__project__owner=self.request.user).order_by('status', '-created_at')

@login_required
@require_POST
def advance_project_phase(request, pk):
    """
    Advances the project to the next phase.
    """
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    
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
    task = get_object_or_404(Task, pk=task_pk, phase__project__owner=request.user)
    new_status = request.POST.get('status')

    if new_status in Task.Status.values:
        task.status = new_status
        task.save()
        messages.success(request, _("Task status updated successfully."))
    else:
        messages.error(request, _("Invalid status provided."))

    # Redirect back to the referrer page (e.g., task list or project detail)
    # or a default view if the referrer is not available.
    return redirect(request.META.get('HTTP_REFERER', reverse_lazy('projects:task-list')))


@login_required
@require_POST
def task_create(request, project_pk):
    """
    Handles the creation of a new task for a specific project.
    """
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    
    # Ensure the project has at least one phase
    phase_id = request.POST.get('phase')
    if not phase_id:
        messages.error(request, _("Could not determine the phase for the new task."))
        return redirect('projects:project-detail', pk=project.pk)

    phase = get_object_or_404(project.phases, id=phase_id)

    form = TaskForm(request.POST)

    if form.is_valid():
        task = form.save(commit=False)
        task.phase = phase
        task.save()
        messages.success(request, _("Task created successfully."))
    else:
        # If the form is invalid, the errors will be stored in the form instance.
        # It's good practice to display these errors to the user.
        # For simplicity, we'll just show a generic error message.
        # A better implementation would re-render the detail page with the form and its errors.
        messages.error(request, _("There was an error creating the task. Please check the data."))

    return redirect('projects:project-detail', pk=project.pk)
