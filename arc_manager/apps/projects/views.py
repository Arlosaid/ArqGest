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

# Task Views
@login_required
def task_create(request, project_pk):
    # Dummy implementation
    return HttpResponse("Task create view")

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'

class MyTaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/my_tasks.html'
    context_object_name = 'tasks'

@login_required
@require_POST
def update_task_status(request, task_pk):
    # Dummy implementation
    return HttpResponse("Update task status view")

@login_required
@require_POST
def move_task(request, task_pk):
    # Dummy implementation
    return HttpResponse("Move task view")

@login_required
def task_edit(request, pk):
    # Dummy implementation
    return HttpResponse("Task edit view")

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
