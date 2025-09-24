"""
Utilidades de cache específicas para proyectos
Funciones para invalidar cache cuando se modifican datos
"""
from django.core.cache import cache


def invalidate_project_cache(organization_id, project_id=None):
    """
    Invalida el cache relacionado con proyectos de una organización
    Args:
        organization_id: ID de la organización
        project_id: ID del proyecto específico (opcional)
    """
    cache_keys = [
        f"project_list_stats:{organization_id}",
        f"dashboard_stats:{organization_id}",
        f"dashboard_projects_progress:{organization_id}",
        f"org_subscription:{organization_id}",
    ]
    
    # Si se especifica un proyecto, invalidar su cache específico
    if project_id:
        cache_keys.extend([
            f"project_detail_stats:{project_id}",
            f"project_kanban_stats:{project_id}",
            f"project_progress:{project_id}",
        ])
    
    cache.delete_many(cache_keys)


def invalidate_task_cache(organization_id, project_id, user_id=None):
    """
    Invalida el cache relacionado con tareas
    Args:
        organization_id: ID de la organización
        project_id: ID del proyecto
        user_id: ID del usuario (para cache de "mis tareas")
    """
    cache_keys = [
        f"project_detail_stats:{project_id}",
        f"project_kanban_stats:{project_id}",
        f"dashboard_stats:{organization_id}",
        f"dashboard_projects_progress:{organization_id}",  # Agregado para dashboard
        f"project_progress:{project_id}",  # Agregado para progreso específico
    ]
    
    # Si se especifica un usuario, invalidar su cache de tareas
    if user_id:
        cache_keys.append(f"my_tasks_stats:{user_id}")
    
    cache.delete_many(cache_keys)


def get_or_set_project_stats(project_id, calculate_func, timeout=300):
    """
    Obtiene estadísticas de proyecto desde cache o las calcula
    Args:
        project_id: ID del proyecto
        calculate_func: Función que calcula las estadísticas
        timeout: Tiempo de cache en segundos (default: 5 minutos)
    """
    cache_key = f"project_detail_stats:{project_id}"
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = calculate_func()
        cache.set(cache_key, stats, timeout)
    
    return stats


def cache_project_method(timeout=300):
    """
    Decorador para cachear métodos de modelos de proyectos
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            cache_key = f"project_method:{self.id}:{func.__name__}"
            result = cache.get(cache_key)
            
            if result is None:
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def get_or_set_project_progress(project_id, timeout=600):
    """
    Obtiene el progreso de un proyecto desde cache o lo calcula.
    Usa cache de 10 minutos para optimizar rendimiento.
    """
    cache_key = f"project_progress:{project_id}"
    progress = cache.get(cache_key)
    
    if progress is None:
        # Importar aquí para evitar dependencias circulares
        from django.db.models import Count, Q
        from .models import Task
        
        # Cálculo optimizado con una sola consulta
        stats = Task.objects.filter(phase__project_id=project_id).aggregate(
            total=Count('id'),
            done=Count('id', filter=Q(status='DONE'))
        )
        
        if stats['total'] == 0:
            progress = 0
        else:
            progress = int((stats['done'] / stats['total']) * 100)
        
        # Cache por 10 minutos
        cache.set(cache_key, progress, timeout)
    
    return progress


def invalidate_project_progress_cache(project_id):
    """
    Invalida específicamente el cache de progreso de un proyecto.
    Se debe llamar cuando se modifica el estado de cualquier tarea.
    """
    cache_key = f"project_progress:{project_id}"
    cache.delete(cache_key)


def get_or_set_dashboard_projects_progress(organization_id, timeout=600):
    """
    Obtiene el progreso de todos los proyectos para el dashboard.
    Optimizado para mostrar múltiples proyectos con un solo cache.
    """
    cache_key = f"dashboard_projects_progress:{organization_id}"
    progress_data = cache.get(cache_key)
    
    if progress_data is None:
        from django.db.models import Count, Q
        from .models import Project, Task
        
        # Obtener todos los proyectos activos de la organización
        projects = Project.objects.filter(
            organization_id=organization_id,
            status='ACTIVE'
        ).values_list('id', flat=True)
        
        progress_data = {}
        
        # Calcular progreso para cada proyecto en una consulta optimizada
        for project_id in projects:
            stats = Task.objects.filter(phase__project_id=project_id).aggregate(
                total=Count('id'),
                done=Count('id', filter=Q(status='DONE'))
            )
            
            if stats['total'] == 0:
                progress_data[project_id] = 0
            else:
                progress_data[project_id] = int((stats['done'] / stats['total']) * 100)
        
        # Cache por 10 minutos
        cache.set(cache_key, progress_data, timeout)
    
    return progress_data


def get_or_set_user_accessible_projects(user_id, organization_id, is_admin=False, timeout=600):
    """
    SOLUCIÓN ÓPTIMA: Obtiene solo los proyectos que el usuario puede acceder.
    Elimina la necesidad de mostrar proyectos sin acceso.
    
    Args:
        user_id: ID del usuario
        organization_id: ID de la organización
        is_admin: Si es admin, puede acceder a todos los proyectos
        timeout: Tiempo de cache en segundos (default: 10 minutos)
    
    Returns:
        dict: {
            'active_ids': set,     # IDs de proyectos activos accesibles
            'completed_ids': set,  # IDs de proyectos completados accesibles
            'archived_ids': set    # IDs de proyectos archivados accesibles
        }
    """
    cache_key = f"user_accessible_projects:{user_id}:{organization_id}:{is_admin}"
    accessible_projects = cache.get(cache_key)
    
    if accessible_projects is None:
        from .models import Project
        
        if is_admin:
            # Admins ven todos los proyectos
            all_projects = Project.objects.filter(organization_id=organization_id)
            active_ids = set(all_projects.filter(status='ACTIVE').values_list('id', flat=True))
            completed_ids = set(all_projects.filter(status='COMPLETED').values_list('id', flat=True))
            archived_ids = set(all_projects.filter(status='ARCHIVED').values_list('id', flat=True))
        else:
            # Usuarios normales ven:
            # - Proyectos donde tienen tareas asignadas
            # - Proyectos donde son propietarios (owner)
            projects_with_tasks = Project.objects.filter(
                organization_id=organization_id,
                phases__tasks__assigned_to_id=user_id,
            )
            projects_owned = Project.objects.filter(
                organization_id=organization_id,
                owner_id=user_id,
            )
            projects_qs = (projects_with_tasks | projects_owned).distinct()
            
            active_ids = set(projects_qs.filter(status='ACTIVE').values_list('id', flat=True))
            completed_ids = set(projects_qs.filter(status='COMPLETED').values_list('id', flat=True))
            archived_ids = set(projects_qs.filter(status='ARCHIVED').values_list('id', flat=True))
        
        accessible_projects = {
            'active_ids': active_ids,
            'completed_ids': completed_ids,
            'archived_ids': archived_ids,
            'total_count': len(active_ids) + len(completed_ids) + len(archived_ids)
        }
        
        # Cache por 10 minutos (más tiempo porque es más estable)
        cache.set(cache_key, accessible_projects, timeout)
    
    return accessible_projects


def invalidate_user_accessible_projects_cache(user_id, organization_id=None, is_admin=False):
    """
    Invalida el cache de proyectos accesibles de un usuario.
    Se debe llamar cuando se asigna o desasigna una tarea.
    
    Args:
        user_id: ID del usuario
        organization_id: ID de la organización (opcional, para optimizar)
        is_admin: Si es admin (opcional, para optimizar)
    """
    if organization_id:
        # Invalidar cache específico
        cache_key = f"user_accessible_projects:{user_id}:{organization_id}:{is_admin}"
        cache.delete(cache_key)
        
        # También invalidar cache del admin si es diferente
        if not is_admin:
            admin_cache_key = f"user_accessible_projects:{user_id}:{organization_id}:True"
            cache.delete(admin_cache_key)
    
    # También invalidar cache de tareas del usuario
    cache.delete(f"my_tasks_stats:{user_id}")


def get_or_set_kanban_projects_data(organization_id, timeout=600):
    """
    Obtiene todos los datos necesarios para el selector de Kanban.
    Cache consolidado para optimizar múltiples consultas.
    
    Args:
        organization_id: ID de la organización
        timeout: Tiempo de cache en segundos (default: 10 minutos)
    
    Returns:
        dict: {
            'active_projects': QuerySet de proyectos activos,
            'completed_projects': QuerySet de proyectos completados,
            'archived_projects': QuerySet de proyectos archivados,
            'total_count': int
        }
    """
    cache_key = f"kanban_projects_data:{organization_id}"
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        from .models import Project
        
        # Una sola query para obtener todos los proyectos
        all_projects = Project.objects.filter(organization_id=organization_id)
        
        # Separar por estado (esto es rápido en memoria)
        active_projects = all_projects.filter(status='ACTIVE')
        completed_projects = all_projects.filter(status='COMPLETED')
        archived_projects = all_projects.filter(status='ARCHIVED')
        
        cached_data = {
            'active_projects': list(active_projects.values_list('id', flat=True)),
            'completed_projects': list(completed_projects.values_list('id', flat=True)),
            'archived_projects': list(archived_projects.values_list('id', flat=True)),
            'total_count': all_projects.count()
        }
        
        # Cache por 10 minutos
        cache.set(cache_key, cached_data, timeout)
    
    return cached_data


def invalidate_kanban_projects_cache(organization_id):
    """
    Invalida el cache de datos del selector de Kanban.
    Se debe llamar cuando se crean, modifican o eliminan proyectos.
    """
    cache_key = f"kanban_projects_data:{organization_id}"
    cache.delete(cache_key)


def get_user_accessible_projects(user, organization):
    """
    Obtiene un QuerySet de proyectos accesibles para un usuario.
    Esta función es un wrapper de get_or_set_user_accessible_projects
    que devuelve un QuerySet en lugar de IDs.
    
    Args:
        user: Usuario actual
        organization: Organización del usuario
    
    Returns:
        QuerySet: Proyectos accesibles para el usuario
    """
    from .models import Project
    
    # Obtener IDs de proyectos accesibles
    accessible_data = get_or_set_user_accessible_projects(
        user.id, 
        organization.id, 
        user.is_org_admin
    )
    
    # Combinar todos los IDs accesibles
    all_accessible_ids = (
        accessible_data['active_ids'] | 
        accessible_data['completed_ids'] | 
        accessible_data['archived_ids']
    )
    
    # Devolver QuerySet con proyectos accesibles
    return Project.objects.filter(
        id__in=all_accessible_ids,
        organization=organization
    )