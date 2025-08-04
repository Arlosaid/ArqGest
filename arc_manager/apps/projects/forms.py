# arc_manager/apps/projects/forms.py
from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    """
    Form for creating and updating tasks.
    """
    class Meta:
        model = Task
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a description...'}),
        }
