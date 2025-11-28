"""
Utilidades de caché para archivos
Maneja la invalidación inteligente del caché Redis
"""
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def invalidate_phase_files_cache(phase_id):
    """
    Invalida todo el caché de archivos para una fase específica.
    Se llama cuando se suben, eliminan o modifican archivos.
    """
    try:
        # Patrón para encontrar todas las claves de caché de esta fase
        cache_pattern = f"files_phase_{phase_id}_*"
        
        # En Redis, usamos el método delete_pattern de django-redis
        cache.delete_pattern(cache_pattern)
        
        logger.debug(f"Cache invalidado para fase {phase_id}")
        return True
        
    except Exception as e:
        logger.warning(f"Error invalidando cache para fase {phase_id}: {e}")
        return False

def get_cache_key(phase_id, offset=0, limit=18, file_type_filter='', date_filter=''):
    """
    Genera clave de caché consistente para consultas de archivos
    """
    # OPTIMIZACIÓN: Hash para claves muy largas
    import hashlib
    key_components = f"{phase_id}_{offset}_{limit}_{file_type_filter}_{date_filter}"
    if len(key_components) > 200:  # Límite de Redis para claves
        key_hash = hashlib.md5(key_components.encode()).hexdigest()
        return f"files_phase_{key_hash}"
    return f"files_phase_{key_components}"

def cache_files_result(phase_id, files_data, has_more, offset=0, limit=18, 
                      file_type_filter='', date_filter='', timeout=600):
    """
    Guarda resultado de archivos en caché Redis
    """
    try:
        cache_key = get_cache_key(phase_id, offset, limit, file_type_filter, date_filter)
        cache.set(cache_key, (files_data, has_more), timeout)
        return True
    except Exception as e:
        logger.warning(f"Error guardando en cache: {e}")
        return False

def get_cached_files_result(phase_id, offset=0, limit=18, file_type_filter='', date_filter=''):
    """
    Obtiene resultado de archivos desde caché Redis
    """
    try:
        cache_key = get_cache_key(phase_id, offset, limit, file_type_filter, date_filter)
        return cache.get(cache_key)
    except Exception as e:
        logger.warning(f"Error obteniendo desde cache: {e}")
        return None
