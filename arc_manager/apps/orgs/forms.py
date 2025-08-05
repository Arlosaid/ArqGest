from django import forms
from .models import Organization, Client
from apps.plans.models import Plan
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit

class ClientForm(forms.ModelForm):
    """
    Formulario para crear y editar Clientes.
    """
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone_number', 'address', 'is_active']

    def __init__(self, *args, **kwargs):
        kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-control', placeholder='Nombre completo o Razón Social'),
            Field('email', css_class='form-control', placeholder='correo@ejemplo.com'),
            Field('phone_number', css_class='form-control', placeholder='+52 1 234 567 890'),
            Field('address', css_class='form-control', rows='3', placeholder='Dirección completa'),
            Field('is_active', css_class='form-check-input'),
            Submit('submit', 'Guardar Cliente', css_class='btn btn-primary mt-3')
        )


class OrganizationForm(forms.ModelForm):
    """Formulario para crear y editar organizaciones"""
    
    initial_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True).order_by('price', 'max_users'),
        required=True,
        empty_label=None,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-toggle': 'tooltip',
            'title': 'El plan determina automáticamente el límite de usuarios y características disponibles'
        }),
        help_text="Selecciona el plan inicial para la organización. Se creará automáticamente una suscripción."
    )
    
    class Meta:
        model = Organization
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la organización'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la organización'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            try:
                trial_plan = Plan.objects.get(name='trial', is_active=True)
                self.fields['initial_plan'].initial = trial_plan.pk
                self.fields['initial_plan'].help_text = "Se creará automáticamente una suscripción de prueba gratuita de 30 días."
            except Plan.DoesNotExist:
                try:
                    basic_plan = Plan.objects.get(name='basic', is_active=True)
                    self.fields['initial_plan'].initial = basic_plan.pk
                except Plan.DoesNotExist:
                    pass
        else:
            if 'initial_plan' in self.fields:
                del self.fields['initial_plan']
    

    
    def clean_initial_plan(self):
        if not self.instance.pk:
            plan = self.cleaned_data.get('initial_plan')
            if not plan:
                raise forms.ValidationError("Debes seleccionar un plan inicial.")
            return plan
        return None
    
    def save(self, commit=True):
        """Sobrescribir save para crear la suscripción automáticamente"""
        from apps.plans.models import Subscription
        
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            if not hasattr(instance, 'subscription'):
                initial_plan = self.cleaned_data.get('initial_plan')
                if initial_plan:
                    Subscription.objects.create(
                        organization=instance,
                        plan=initial_plan
                    )
        
        return instance
