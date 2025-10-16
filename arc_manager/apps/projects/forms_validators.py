"""
Validaciones personalizadas para formularios de proyectos.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.validators import validate_end_date_after_start_date


def clean_project_dates(cleaned_data):
    """
    Valida que las fechas del proyecto sean coherentes.
    """
    start_date = cleaned_data.get('start_date')
    end_date = cleaned_data.get('end_date')
    
    if start_date and end_date:
        try:
            validate_end_date_after_start_date(start_date, end_date)
        except ValidationError as e:
            raise ValidationError({
                'end_date': e.message
            })
    
    return cleaned_data


def clean_phase_dates(cleaned_data):
    """
    Valida que las fechas de la fase sean coherentes.
    """
    start_date = cleaned_data.get('start_date')
    end_date = cleaned_data.get('end_date')
    
    if start_date and end_date:
        try:
            validate_end_date_after_start_date(start_date, end_date)
        except ValidationError as e:
            raise ValidationError({
                'end_date': e.message
            })
    
    return cleaned_data

