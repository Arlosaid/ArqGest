# arc_manager/apps/projects/forms.py
from django import forms
from .models import Task, Project, ProjectTemplate
from apps.orgs.models import Client

class ProjectForm(forms.ModelForm):
    """
    Form for creating a project, with an option to use a template.
    """
    template = forms.ModelChoiceField(
        queryset=ProjectTemplate.objects.all(),
        required=False,
        label="Crear desde plantilla",
        help_text="Selecciona una plantilla para crear las fases del proyecto automáticamente."
    )

    class Meta:
        model = Project
        fields = ['name', 'client', 'template']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraer el usuario de la organización de los kwargs
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        if organization:
            # Filtrar el queryset de clientes para que solo muestre los de la organización actual
            self.fields['client'].queryset = Client.objects.filter(organization=organization)
        else:
            # Si no hay organización, no mostrar ningún cliente
            self.fields['client'].queryset = Client.objects.none()
            
        # Opcional: Añadir un texto de ayuda o un placeholder
        self.fields['client'].help_text = "Selecciona un cliente de tu organización."
        self.fields['client'].empty_label = "Seleccionar un Cliente"


class TaskForm(forms.ModelForm):
    """
    Form for creating and updating tasks.
    """

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.organization:
            self.fields['assigned_to'].queryset = user.organization.users.all()

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a description...'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
