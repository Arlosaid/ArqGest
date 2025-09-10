# arc_manager/apps/projects/forms.py
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from .models import Task, Project, PhaseTemplate
from apps.orgs.models import Client
from django.forms import formset_factory

class PhaseForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombre de la fase')})
    )
    order = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

class BasePhaseFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si está ligado, desactivar la obligatoriedad de 'name' en formularios marcados para borrar
        if self.is_bound:
            for form in self.forms:
                field_name = form.add_prefix('DELETE')
                try:
                    marked_delete = form.data.get(field_name)
                except AttributeError:
                    marked_delete = None
                if str(marked_delete).lower() in {'on', 'true', '1'}:
                    if 'name' in form.fields:
                        form.fields['name'].required = False

    def clean(self):
        if any(self.errors):
            return
        
        names = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                name = form.cleaned_data.get('name')
                if name in names:
                    raise forms.ValidationError(_("Los nombres de las fases deben ser únicos."))
                names.append(name)

# No forzar un formulario vacío por defecto y manejar el orden manualmente con el campo oculto 'order'
PhaseFormSet = formset_factory(
    PhaseForm,
    formset=BasePhaseFormSet,
    can_delete=True,
    can_order=False,
    extra=0
)

class ProjectForm(forms.ModelForm):
    """
    Formulario para crear un proyecto.
    """
    PHASE_CREATION_CHOICES = [
        ('template', _('Usar una plantilla de fases')),
        ('manual', _('Definir fases manualmente')),
    ]

    phase_creation_method = forms.ChoiceField(
        choices=PHASE_CREATION_CHOICES,
        widget=forms.RadioSelect,
        initial='template',
        label=_("¿Cómo te gustaría crear las fases para este proyecto?")
    )
    phase_template = forms.ModelChoiceField(
        queryset=PhaseTemplate.objects.all(),
        required=False,
        label=_("Plantilla de Fases"),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Project
        fields = ['name', 'client', 'phase_creation_method', 'phase_template']
        labels = {
            'name': _('Nombre del Proyecto'),
            'client': _('Cliente'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields['client'].queryset = Client.objects.filter(organization=organization)
            self.fields['phase_template'].queryset = PhaseTemplate.objects.filter(
                models.Q(organization=organization) | models.Q(organization__isnull=True)
            )
        else:
            self.fields['client'].queryset = Client.objects.none()
            self.fields['phase_template'].queryset = PhaseTemplate.objects.none()
            
        self.fields['client'].help_text = _("Selecciona un cliente de tu organización.")
        self.fields['client'].empty_label = _("Seleccionar un Cliente")

    def clean(self):
        cleaned_data = super().clean()
        creation_method = cleaned_data.get('phase_creation_method')
        phase_template = cleaned_data.get('phase_template')

        if creation_method == 'template' and not phase_template:
            self.add_error('phase_template', _("Este campo es obligatorio cuando se utiliza una plantilla."))

        return cleaned_data


class TaskForm(forms.ModelForm):
    """
    Formulario para crear y actualizar tareas.
    """
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date']
        labels = {
            'title': _('Título'),
            'description': _('Descripción'),
            'assigned_to': _('Asignado a'),
            'priority': _('Prioridad'),
            'due_date': _('Fecha de Vencimiento'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Título de la tarea')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Añade una descripción...')}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Determinar la organización desde user o project
        organization = None
        if user and hasattr(user, 'organization'):
            organization = user.organization
        elif project and hasattr(project, 'organization'):
            organization = project.organization
        
        if organization:
            self.fields['assigned_to'].queryset = organization.users.filter(
                is_active=True, 
                is_superuser=False
            )

class PhaseTemplateForm(forms.ModelForm):
    """Formulario para crear y editar Plantillas de Fase."""
    class Meta:
        model = PhaseTemplate
        fields = ['name', 'description']
        labels = {
            'name': _('Nombre'),
            'description': _('Descripción'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
