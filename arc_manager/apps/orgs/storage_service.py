# apps/orgs/storage_service.py
from django.core.cache import cache
from django.db.models import Sum
from django.conf import settings
from apps.files.models import ProjectFile
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """
    Servicio optimizado para calcular y cachear el uso de almacenamiento por organización.
    Utiliza Redis para evitar cálculos costosos repetitivos.
    """
    
    CACHE_PREFIX = "org_storage"
    # Permite configurar el TTL vía settings (p. ej. ORG_STORAGE_CACHE_TIMEOUT=21600 para 6h)
    CACHE_TIMEOUT = getattr(settings, 'ORG_STORAGE_CACHE_TIMEOUT', 21600)
    
    @classmethod
    def get_cache_key(cls, organization_id):
        """Genera la clave de cache para una organización"""
        return f"{cls.CACHE_PREFIX}:{organization_id}"
    
    @classmethod
    def calculate_storage_usage(cls, organization):
        """
        Calcula el uso total de almacenamiento para una organización.
        Primero intenta obtener del cache, si no existe lo calcula y lo cachea.
        """
        cache_key = cls.get_cache_key(organization.id)
        
        # Intentar obtener del cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Storage data retrieved from cache for org {organization.id}")
            return cached_data
        
        # Calcular desde la base de datos
        logger.debug(f"Calculating storage usage for organization {organization.id}")
        
        try:
            # Calcular la suma total de bytes de todos los archivos de la organización
            total_bytes = ProjectFile.objects.filter(
                phase__project__organization=organization
            ).aggregate(
                total=Sum('size_bytes')
            )['total'] or 0
            
            # Convertir a GB (con 2 decimales)
            total_gb = round(total_bytes / (1024 ** 3), 2)
            
            # Obtener límite total (plan + extras)
            plan_limit_gb = organization.get_total_storage_limit_gb()
            
            # Calcular porcentaje de uso
            usage_percentage = min(100, round((total_gb / plan_limit_gb) * 100, 1)) if plan_limit_gb > 0 else 100
            
            # Contar archivos
            file_count = ProjectFile.objects.filter(
                phase__project__organization=organization
            ).count()
            
            storage_data = {
                'total_bytes': total_bytes,
                'total_gb': total_gb,
                'plan_limit_gb': plan_limit_gb,
                'usage_percentage': usage_percentage,
                'file_count': file_count,
                'remaining_gb': max(0, plan_limit_gb - total_gb),
                'is_over_limit': total_gb > plan_limit_gb
            }
            
            # Cachear el resultado
            cache.set(cache_key, storage_data, cls.CACHE_TIMEOUT)
            
            logger.debug(f"Storage calculated for org {organization.id}: {total_gb}GB of {plan_limit_gb}GB ({usage_percentage}%)")
            
            return storage_data
            
        except Exception as e:
            logger.error(f"Error calculating storage for organization {organization.id}: {str(e)}")
            # Retornar datos de error/fallback
            return {
                'total_bytes': 0,
                'total_gb': 0,
                'plan_limit_gb': 75,
                'usage_percentage': 0,
                'file_count': 0,
                'remaining_gb': 75,
                'is_over_limit': False,
                'error': True
            }
    
    @classmethod
    def invalidate_cache(cls, organization_id):
        """Invalida el cache de una organización específica"""
        cache_key = cls.get_cache_key(organization_id)
        cache.delete(cache_key)
        logger.debug(f"Storage cache invalidated for organization {organization_id}")
    
    @classmethod
    def get_storage_summary(cls, organization):
        """
        Obtiene un resumen optimizado del almacenamiento para mostrar en UI
        """
        data = cls.calculate_storage_usage(organization)
        
        # Determinar el estado del almacenamiento
        status = 'normal'
        if data['usage_percentage'] >= 90:
            status = 'critical'
        elif data['usage_percentage'] >= 75:
            status = 'warning'
        
        return {
            'used_gb': round(data['total_gb'], 2),
            'total_gb': data['plan_limit_gb'],
            'percentage': round(data['usage_percentage']),
            'remaining_gb': round(data['remaining_gb'], 2),
            'file_count': data['file_count'],
            'status': status,
            'is_over_limit': data['is_over_limit']
        }
    
    @classmethod
    def can_upload_file(cls, organization, file_size_bytes):
        """
        Verifica si una organización puede subir un archivo de cierto tamaño.
        Retorna (puede_subir: bool, mensaje_error: str, datos_almacenamiento: dict)
        """
        storage_data = cls.calculate_storage_usage(organization)
        
        # Convertir el tamaño del archivo a GB
        file_size_gb = file_size_bytes / (1024 ** 3)
        
        # Calcular el nuevo total si se sube el archivo
        new_total_gb = storage_data['total_gb'] + file_size_gb
        
        # Verificar si excedería el límite
        if new_total_gb > storage_data['plan_limit_gb']:
            remaining_gb = storage_data['remaining_gb']
            file_size_mb = round(file_size_bytes / (1024 ** 2), 2)
            remaining_mb = round(remaining_gb * 1024, 2)
            
            error_msg = (
                f"No se puede subir el archivo ({file_size_mb} MB). "
                f"Solo tienes {remaining_mb} MB disponibles de tu límite de "
                f"{storage_data['plan_limit_gb']} GB."
            )
            
            logger.warning(
                f"Upload blocked for org {organization.id}: file size {file_size_mb}MB "
                f"exceeds remaining storage {remaining_mb}MB"
            )
            
            return False, error_msg, storage_data
        
        # Se puede subir
        return True, "", storage_data
    
    @classmethod
    def format_size(cls, bytes_size):
        """Formatea el tamaño en bytes a una representación legible"""
        if bytes_size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(bytes_size, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_size / p, 2)
        return f"{s} {size_names[i]}"
