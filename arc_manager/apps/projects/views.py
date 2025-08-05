from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView
)
from .models import Project, Task, Phase, PhaseTemplate
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import TaskForm, ProjectForm, PhaseTemplateForm, PhaseFormSet
from django.db.models import Count


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
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Project.objects.filter(
                organization=self.request.user.organization
            ).select_related('client', 'owner').order_by('-created_at')
        return Project.objects.none()

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
        response = super().form_valid(form)

        phases_to_create = []
        if creation_method == 'template':
            phase_template = form.cleaned_data.get('phase_template')
            if phase_template:
                phases_to_create = [
                    Phase(project=self.object, name=phase['name'], order=phase['order'])
                    for phase in phase_template.phases
                ]
        elif creation_method == 'manual':
            for phase_form in phase_formset:
                if phase_form.cleaned_data and not phase_form.cleaned_data.get('DELETE'):
                    phases_to_create.append(
                        Phase(
                            project=self.object,
                            name=phase_form.cleaned_data['name'],
                            order=phase_form.cleaned_data['order']
                        )
                    )
        else: # Default fallback
            default_phase_names = [
                _("Estudios Preliminares"), 
                _("Anteproyecto"), 
                _("Proyecto Básico y de Ejecución"), 
                _("Licitación y Contratación"), 
                _("Dirección de Obra")
            ]
            phases_to_create = [
                Phase(project=self.object, name=str(phase_name), order=i)
                for i, phase_name in enumerate(default_phase_names)
            ]
            
        if phases_to_create:
            Phase.objects.bulk_create(phases_to_create)
        
        return response

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        context['phases'] = project.phases.order_by('order')
        context['tasks'] = Task.objects.filter(phase__project=project)
        context['files'] = []
        for phase in context['phases']:
            context['files'].extend(phase.files.all())

        context['task_form'] = TaskForm(user=self.request.user)
        return context

    def test_func(self):
        project = self.get_object()
        return self.request.user.organization == project.organization

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def get_form_kwargs(self):
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
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
            return Task.objects.filter(
                phase__project__organization=self.request.user.organization
            ).select_related(
                'phase__project', 
                'phase__project__client', 
                'assigned_to'
            ).order_by('status', '-created_at')
        return Task.objects.none()


@login_required
@require_POST
def update_task_status(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, phase__project__owner__organization=request.user.organization)
    new_status = request.POST.get('status')

    if new_status in Task.Status.values:
        task.status = new_status
        task.save()
        messages.success(request, _("Estado de la tarea actualizado correctamente."))
    else:
        messages.error(request, _("Se proporcionó un estado no válido."))

    return redirect(request.META.get('HTTP_REFERER', reverse_lazy('projects:task-list')))


@login_required
@require_POST
def task_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, owner__organization=request.user.organization)
    
    phase_id = request.POST.get('phase')
    if not phase_id:
        messages.error(request, _("No se pudo determinar la fase para la nueva tarea."))
        return redirect('projects:project-detail', pk=project.pk)

    phase = get_object_or_404(Phase, id=phase_id, project=project)
    
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
        messages.success(request, _("Tarea creada correctamente."))
        
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse_lazy('projects:project-detail', kwargs={'pk': project.pk})
        return response
    else:
        messages.error(request, _("Hubo un error al crear la tarea. Por favor, comprueba los datos."))
        
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
    try:
        task = get_object_or_404(Task, pk=task_pk, phase__project__owner__organization=request.user.organization)
        
        new_phase_id = request.POST.get('phase_id')
        if not new_phase_id:
            return HttpResponseBadRequest(_("Falta el ID de la fase."))

        new_phase = get_object_or_404(Phase, pk=new_phase_id, project__owner__organization=request.user.organization)

        task.phase = new_phase
        task.save(update_fields=['phase'])

        return HttpResponse(status=200)

    except Exception as e:
        print(f"Error al mover la tarea: {e}")
        return HttpResponseBadRequest(_("Ocurrió un error al mover la tarea."))

class MyTaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/my_tasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(
            assigned_to=self.request.user
        ).select_related(
            'phase__project', 
            'phase__project__client'
        ).order_by('due_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tasks'] = self.get_queryset().count()
        return context

class PhaseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Phase
    template_name = 'projects/phase_kanban.html'
    context_object_name = 'phase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phase = self.get_object()
        project_pk = self.kwargs.get('project_pk')
        
        if phase.project.pk != project_pk:
            raise Http404(_("La fase no pertenece al proyecto especificado."))

        context['project'] = phase.project
        context['tasks'] = phase.tasks.all()
        context['task_status_choices'] = Task.Status.choices
        context['task_form'] = TaskForm(user=self.request.user)
        return context

    def test_func(self):
        phase = self.get_object()
        return self.request.user.organization == phase.project.organization



# Phase Template Views
class PhaseTemplateListView(LoginRequiredMixin, ListView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return PhaseTemplate.objects.filter(organization=self.request.user.organization)



class PhaseTemplateCreateView(LoginRequiredMixin, CreateView):
    model = PhaseTemplate
    form_class = PhaseTemplateForm
    template_name = 'projects/phasetemplate_form.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

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
        
        if phase_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.organization = self.request.user.organization
            
            phases = []
            for phase_form in phase_formset:
                if phase_form.cleaned_data and not phase_form.cleaned_data.get('DELETE'):
                    phases.append({
                        'name': phase_form.cleaned_data['name'],
                        'order': phase_form.cleaned_data['order']
                    })
            
            self.object.phases = sorted(phases, key=lambda x: x['order'])
            self.object.save()
            
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class PhaseTemplateDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_detail.html'
    context_object_name = 'template'

    def test_func(self):
        return self.get_object().organization == self.request.user.organization

class PhaseTemplateUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PhaseTemplate
    form_class = PhaseTemplateForm
    template_name = 'projects/phasetemplate_form.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['phase_formset'] = PhaseFormSet(self.request.POST, prefix='phases')
        else:
            initial_phases = self.object.phases or []
            context['phase_formset'] = PhaseFormSet(prefix='phases', initial=initial_phases)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        phase_formset = context['phase_formset']

        if phase_formset.is_valid():
            self.object = form.save(commit=False)
            
            phases = []
            for phase_form in phase_formset:
                if phase_form.cleaned_data and not phase_form.cleaned_data.get('DELETE'):
                    phases.append({
                        'name': phase_form.cleaned_data['name'],
                        'order': phase_form.cleaned_data['order']
                    })
            
            self.object.phases = sorted(phases, key=lambda x: x['order'])
            self.object.save()
            
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
        return self.get_object().organization == self.request.user.organization

class PhaseTemplateDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PhaseTemplate
    template_name = 'projects/phasetemplate_confirm_delete.html'
    success_url = reverse_lazy('projects:phasetemplate-list')

    def test_func(self):
        return self.get_object().organization == self.request.user.organization
