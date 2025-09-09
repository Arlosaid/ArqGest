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
        f"org_subscription:{organization_id}",
    ]
    
    # Si se especifica un proyecto, invalidar su cache específico
    if project_id:
        cache_keys.extend([
            f"project_detail_stats:{project_id}",
            f"project_kanban_stats:{project_id}",
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
