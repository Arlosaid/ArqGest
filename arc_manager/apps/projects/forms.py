# arc_manager/apps/projects/forms.py
from django import forms
from .models import Task, Project, ProjectTemplate

class ProjectForm(forms.ModelForm):
    """
    Form for creating a project, with an option to use a template.
    """
    template = forms.ModelChoiceField(
        queryset=ProjectTemplate.objects.all(),
        required=False,
        label="Create from template",
        help_text="Select a template to automatically create project phases."
    )

    class Meta:
        model = Project
        fields = ['name', 'client', 'template']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.TextInput(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
        }


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
