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
        Ensure users can only see their own projects.
        """
        return Project.objects.filter(owner=self.request.user).order_by('-created_at')

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def form_valid(self, form):
        """
        Assign the current user as the owner and create phases from a template if selected.
        """
        form.instance.owner = self.request.user
        
        # Call the superclass's form_valid to save the object and get the redirect response
        self.object = form.save()

        template = form.cleaned_data.get('template')
        if template:
            phase_templates = template.phase_templates.all().order_by('order')
            for phase_template in phase_templates:
                Phase.objects.create(
                    project=self.object,
                    name=phase_template.name,
                    order=phase_template.order
                )
        
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

        # We need a clean form for the "quick add" functionality in each phase footer.
        # If the view is being re-rendered due to a validation error in `task_create`,
        # the context will contain an invalid form instance. We check for it.
        context['phases'] = phases
        if 'task_form' not in context:
            context['task_form'] = TaskForm(user=self.request.user)
            
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
    
    phase_id = request.POST.get('phase')
    if not phase_id:
        messages.error(request, _("Could not determine the phase for the new task."))
        return redirect('projects:project-detail', pk=project.pk)

    phase = get_object_or_404(project.phases, id=phase_id)
    form = TaskForm(request.POST, user=request.user)

    if form.is_valid():
        task = form.save(commit=False)
        task.phase = phase
        task.save()
        messages.success(request, _("Task created successfully."))
        
        # Instead of a standard redirect, send a response with a header
        # that HTMX will use to redirect the whole page.
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse_lazy('projects:project-detail', kwargs={'pk': project.pk})
        return response
    else:
        # If the form is invalid, re-render the detail page with the form and its errors.
        messages.error(request, _("There was an error creating the task. Please check the data."))
        
        # We need to gather the context again for the detail view
        phases = project.phases.order_by('order').prefetch_related('tasks')
        
        # To display the errors, we need to inject the invalid form into the context,
        # but only for the specific phase where the user tried to add the task.
        context = {
            'project': project,
            'phases': phases,
            'task_form': form,  # The invalid form with its errors
            'error_phase_id': phase.id  # To know where to display the form with errors
        }
        return render(request, 'projects/project_detail.html', context)

@login_required
@require_POST
def move_task(request, task_pk):
    """
    Handles moving a task to a new phase via HTMX.
    """
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__owner=request.user)
        
        new_phase_id = request.POST.get('phase_id')
        if not new_phase_id:
            return HttpResponseBadRequest("Phase ID is missing.")

        new_phase = get_object_or_404(Phase, pk=new_phase_id, project__owner=request.user)

        # Update the task's phase
        task.phase = new_phase
        task.save(update_fields=['phase'])

        return HttpResponse(status=200)

    except Exception as e:
        # Log the error for debugging
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
