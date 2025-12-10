from django import forms
from .models import Organization, Client
from apps.plans.models import Plan
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from core.validators import (
    validate_client_name, 
    validate_organization_name,
    validate_phone_number,
    validate_business_email
)

class ClientForm(forms.ModelForm):
    """
    Formulario para crear y editar Clientes.
    """
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone_number', 'address', 'is_active']

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        # Guardar organización para validaciones y asignación en save
        self.organization = organization or getattr(self.instance, 'organization', None)
        
        # Agregar validadores
        if 'name' in self.fields:
            self.fields['name'].validators.append(validate_client_name)
        if 'email' in self.fields:
            self.fields['email'].validators.append(validate_business_email)
        if 'phone_number' in self.fields:
            self.fields['phone_number'].validators.append(validate_phone_number)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-control', placeholder='Nombre completo o Razón Social',
                  **{'data-char-counter': 'true', 'data-max-length': '100'}),
            Field('email', css_class='form-control', placeholder='correo@ejemplo.com'),
            Field('phone_number', css_class='form-control', placeholder='123 456 7890'),
            Field('address', css_class='form-control', rows='3', placeholder='Dirección completa'),
            Field('is_active', css_class='form-check-input'),
            Submit('submit', 'Guardar Cliente', css_class='btn btn-primary mt-3')
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not self.organization:
            return name

        # Validar unicidad por organización (case-insensitive)
        qs = Client.objects.filter(organization=self.organization, name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un cliente con este nombre en tu organización.')
        return name

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not getattr(instance, 'organization_id', None) and self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance


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
                'placeholder': 'Nombre de la organización',
                'data-char-counter': 'true',
                'data-max-length': '100'
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
        
        # Agregar validador al campo name
        if 'name' in self.fields:
            self.fields['name'].validators.append(validate_organization_name)
        
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
