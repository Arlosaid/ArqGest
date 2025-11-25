# arc_manager/apps/projects/forms.py
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from .models import Task, Project, PhaseTemplate
from apps.orgs.models import Client
from django.forms import formset_factory
from core.validators import (
    validate_project_name, 
    validate_task_title, 
    validate_phase_name,
    validate_end_date_after_start_date,
    validate_budget_amount,
    validate_date_not_too_far_future
)

class PhaseForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        validators=[validate_phase_name],
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': _('Nombre de la fase'),
            'data-char-counter': 'true',
            'data-max-length': '100'
        })
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
    save_as_template = forms.BooleanField(
        required=False,
        label=_("Guardar estas fases como plantilla"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    template_name = forms.CharField(
        required=False,
        label=_("Nombre de la plantilla"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Ej: Proyecto Residencial Básico")})
    )

    class Meta:
        model = Project
        fields = ['name', 'client', 'total_budget', 'phase_creation_method', 'phase_template', 'save_as_template', 'template_name']
        labels = {
            'name': _('Nombre del Proyecto'),
            'client': _('Cliente'),
            'total_budget': _('Presupuesto Total'),
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'data-char-counter': 'true',
                'data-max-length': '100',
                'placeholder': _('Ej: Casa Residencial San Miguel')
            }),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'total_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Agregar validador al campo name
        if 'name' in self.fields:
            self.fields['name'].validators.append(validate_project_name)

        # En edición, remover campos de configuración de fases para evitar validaciones innecesarias
        if getattr(self.instance, 'pk', None):
            self.fields.pop('phase_creation_method', None)
            self.fields.pop('phase_template', None)
            self.fields.pop('save_as_template', None)
            self.fields.pop('template_name', None)

        if organization:
            self.fields['client'].queryset = Client.objects.filter(organization=organization, is_active=True)
            if 'phase_template' in self.fields:
                self.fields['phase_template'].queryset = PhaseTemplate.objects.filter(
                    models.Q(organization=organization) | models.Q(organization__isnull=True)
                )
        else:
            self.fields['client'].queryset = Client.objects.none()
            if 'phase_template' in self.fields:
                self.fields['phase_template'].queryset = PhaseTemplate.objects.none()
            
        self.fields['client'].help_text = _("Selecciona un cliente de tu organización.")
        self.fields['client'].empty_label = _("Seleccionar un Cliente")

    def clean(self):
        cleaned_data = super().clean()
        creation_method = cleaned_data.get('phase_creation_method')
        phase_template = cleaned_data.get('phase_template')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        total_budget = cleaned_data.get('total_budget')

        # Solo aplicar esta validación al CREAR proyectos.
        if not getattr(self.instance, 'pk', None):
            if creation_method == 'template' and not phase_template:
                self.add_error('phase_template', _("Este campo es obligatorio cuando se utiliza una plantilla."))

        # Validar fechas
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _("La fecha de fin debe ser posterior a la fecha de inicio."))
        
        # Validar presupuesto
        if total_budget is not None:
            from core.validators import validate_budget_amount
            try:
                validate_budget_amount(total_budget)
            except ValidationError as e:
                self.add_error('total_budget', e.message)

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
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Ej: Diseñar planos arquitectónicos'),
                'data-char-counter': 'true',
                'data-max-length': '120'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Añade una descripción...')}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Agregar validador al campo title
        if 'title' in self.fields:
            self.fields['title'].validators.append(validate_task_title)
        
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
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'data-char-counter': 'true',
                'data-max-length': '100',
                'placeholder': _('Ej: Proyecto Residencial Estándar')
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
