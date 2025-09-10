# arc_manager/apps/projects/services.py
from django.utils.translation import gettext_lazy as _
from .models import Phase, Project, PhaseTemplate
import logging

logger = logging.getLogger(__name__)

def create_phases_for_project(project: Project, creation_method: str, phase_template: PhaseTemplate = None, phase_formset=None):
    """
    Crea las fases para un proyecto basado en el método de creación especificado.
    """
    logger.info(f"Creating phases for project {project.id} using method: {creation_method}")
    
    phases_to_create = []
    
    if creation_method == 'template' and phase_template:
        logger.debug(f"Using template '{phase_template.name}' (ID: {phase_template.id}) for project {project.id}")
        phases_to_create = [
            Phase(project=project, name=phase['name'], order=phase['order'])
            for phase in phase_template.phases
        ]
        logger.info(f"Prepared {len(phases_to_create)} phases from template for project {project.id}")
        
    elif creation_method == 'manual' and phase_formset and phase_formset.is_valid():
        logger.debug(f"Using manual phase creation for project {project.id}")
        for phase_form in phase_formset:
            if phase_form.cleaned_data and not phase_form.cleaned_data.get('DELETE'):
                phases_to_create.append(
                    Phase(
                        project=project,
                        name=phase_form.cleaned_data['name'],
                        order=phase_form.cleaned_data['order']
                    )
                )
        logger.info(f"Prepared {len(phases_to_create)} manual phases for project {project.id}")
        
    else:  # Default fallback
        logger.debug(f"Using default phase fallback for project {project.id}")
        default_phase_names = [
            _("Estudios Preliminares"),
            _("Anteproyecto"),
            _("Proyecto Básico y de Ejecución"),
            _("Licitación y Contratación"),
            _("Dirección de Obra")
        ]
        phases_to_create = [
            Phase(project=project, name=str(phase_name), order=i)
            for i, phase_name in enumerate(default_phase_names)
        ]
        logger.info(f"Prepared {len(phases_to_create)} default phases for project {project.id}")

    if phases_to_create:
        try:
            Phase.objects.bulk_create(phases_to_create)
            logger.info(f"Successfully created {len(phases_to_create)} phases for project {project.id}")
        except Exception as e:
            logger.error(f"Failed to create phases for project {project.id}: {str(e)}", exc_info=True)
            raise
    else:
        logger.warning(f"No phases to create for project {project.id} - method: {creation_method}")
