from django import template
from django.templatetags.static import static
from django.conf import settings

register = template.Library()


@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key, [])
    except Exception:
        return []


@register.filter(name='dict_get')
def dict_get(value, key):
    """Obtiene value[key] si es un dict; de lo contrario retorna None."""
    try:
        if isinstance(value, dict):
            return value.get(key)
        return None
    except Exception:
        return None


@register.filter(name='cached_progress')
def cached_progress(project):
    """
    Obtiene el progreso desde cache si está disponible, de lo contrario usa el método del modelo.
    Optimizado para el dashboard.
    """
    try:
        # Primero intentar obtener desde cache asignado en la vista
        if hasattr(project, '_cached_progress'):
            return project._cached_progress
        
        # Fallback al método del modelo (que ya usa cache internamente)
        if hasattr(project, 'progress_percentage'):
            return project.progress_percentage
        
        # Si por alguna razón no existe el método, calcularlo directamente
        from django.db.models import Count, Q
        from apps.projects.models import Task
        
        total_tasks = Task.objects.filter(phase__project=project).count()
        if total_tasks == 0:
            return 0
        
        done_tasks = Task.objects.filter(phase__project=project, status='DONE').count()
        return int((done_tasks / total_tasks) * 100)
        
    except Exception as e:
        # Para debugging - mostrar el error en logs
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating progress for project {getattr(project, 'id', 'unknown')}: {e}")
        return 0


@register.filter(name='dashboard_image')
def dashboard_image(project):
    """
    Asigna automáticamente una imagen del dashboard basada en el ID del proyecto.
    Usa números secuenciales para simplicidad.
    """
    try:
        # Total de imágenes disponibles (1.jpg a 6.jpg)
        total_images = 6
        
        # Usar el ID del proyecto para seleccionar una imagen de forma determinística
        if hasattr(project, 'id') and project.id:
            image_number = (project.id % total_images) + 1
            image_url = static(f'images/projects/dashboard/{image_number}.jpg')
        else:
            # Fallback si no hay ID
            image_url = static('images/projects/dashboard/1.jpg')
        
        # Agregar versionado para cache-busting en móviles
        version = getattr(settings, 'STATIC_VERSION', 'v1')
        return f"{image_url}?v={version}"
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting dashboard image for project {getattr(project, 'id', 'unknown')}: {e}")
        image_url = static('images/projects/dashboard/1.jpg')
        version = getattr(settings, 'STATIC_VERSION', 'v1')
        return f"{image_url}?v={version}"


@register.filter(name='versioned_static')
def versioned_static(static_path):
    """
    Agrega versionado automático a cualquier archivo estático para cache-busting.
    Uso: {{ 'css/dashboard.css'|versioned_static }}
    """
    try:
        static_url = static(static_path)
        version = getattr(settings, 'STATIC_VERSION', 'v1')
        return f"{static_url}?v={version}"
    except Exception:
        return static(static_path)


@register.filter(name='sub')
def sub(value, arg):
    """
    Resta arg de value.
    Uso: {{ 502|sub:project.payment_percentage }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='mul')
def mul(value, arg):
    """
    Multiplica value por arg.
    Uso: {{ 50|mul:5.02 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='sum_tasks')
def sum_tasks(phases):
    """
    Cuenta el total de tareas en una lista de fases.
    Uso: {{ project.phases.all|sum_tasks }}
    """
    try:
        from apps.projects.models import Task
        if not phases:
            return 0
        # Obtener IDs de las fases
        phase_ids = [phase.id for phase in phases if hasattr(phase, 'id')]
        if not phase_ids:
            return 0
        return Task.objects.filter(phase_id__in=phase_ids).count()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error counting files: {e}")
        return 0


@register.filter(name='file_icon')
def file_icon(extension):
    """
    Retorna el icono y clase CSS correspondiente a una extensión de archivo.
    Uso: {{ file.extension|file_icon }}
    Las clases corresponden a files-tab.css
    """
    extension = extension.upper() if extension else ''
    
    icons = {
        'PDF': {'icon': 'fas fa-file-pdf', 'class': 'pdf'},
        'JPG': {'icon': 'fas fa-image', 'class': 'image'},
        'JPEG': {'icon': 'fas fa-image', 'class': 'image'},
        'PNG': {'icon': 'fas fa-image', 'class': 'image'},
        'GIF': {'icon': 'fas fa-image', 'class': 'image'},
        'TIFF': {'icon': 'fas fa-image', 'class': 'image'},
        'DWG': {'icon': 'fas fa-drafting-compass', 'class': 'cad'},
        'DXF': {'icon': 'fas fa-drafting-compass', 'class': 'cad'},
        'RVT': {'icon': 'fas fa-building', 'class': 'revit'},
        'SKP': {'icon': 'fas fa-cube', 'class': 'sketchup'},
        'DOC': {'icon': 'fas fa-file-word', 'class': 'word'},
        'DOCX': {'icon': 'fas fa-file-word', 'class': 'word'},
        'XLS': {'icon': 'fas fa-file-excel', 'class': 'excel'},
        'XLSX': {'icon': 'fas fa-file-excel', 'class': 'excel'},
        'PPT': {'icon': 'fas fa-file-powerpoint', 'class': 'ppt'},
        'PPTX': {'icon': 'fas fa-file-powerpoint', 'class': 'ppt'},
        'ZIP': {'icon': 'fas fa-file-zipper', 'class': 'archive'},
        'RAR': {'icon': 'fas fa-file-zipper', 'class': 'archive'},
        'TXT': {'icon': 'fas fa-file-lines', 'class': 'text'},
        'MD': {'icon': 'fas fa-file-lines', 'class': 'text'},
    }
    
    return icons.get(extension, {'icon': 'fas fa-file', 'class': 'default'})


@register.filter(name='sum_files')
def sum_files(phases):
    """
    Cuenta el total de archivos en una lista de fases.
    Uso: {{ project.phases.all|sum_files }}
    """
    try:
        from apps.files.models import ProjectFile
        if not phases:
            return 0
        # Obtener IDs de las fases
        phase_ids = [phase.id for phase in phases if hasattr(phase, 'id')]
        if not phase_ids:
            return 0
        return ProjectFile.objects.filter(phase_id__in=phase_ids).count()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error counting files: {e}")
        return 0


@register.filter(name='can_delete_file')
def can_delete_file(file, user):
    """
    Verifica si el usuario puede eliminar un archivo.
    Retorna True si el usuario es admin o si subió el archivo.
    Funciona con objetos del modelo o diccionarios serializados.
    Uso: {% if file|can_delete_file:user %}
    """
    try:
        if not user or not user.is_authenticated:
            return False
        
        # Si el usuario es admin, puede eliminar cualquier archivo
        if getattr(user, 'is_org_admin', False):
            return True
        
        # Obtener uploaded_by_id del archivo (puede ser objeto o diccionario)
        if isinstance(file, dict):
            uploaded_by_id = file.get('uploaded_by_id')
        else:
            uploaded_by_id = getattr(file, 'uploaded_by_id', None)
        
        # Comparar con el ID del usuario
        if uploaded_by_id is not None and user.id is not None:
            return int(uploaded_by_id) == int(user.id)
        
        return False
    except Exception:
        return False