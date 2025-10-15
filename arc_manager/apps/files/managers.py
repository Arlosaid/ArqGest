# apps/files/managers.py
"""
Manager optimizado para ProjectFile con consultas eficientes
"""
from django.db import models
from django.db.models import Q, Count, Sum
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class ProjectFileQuerySet(models.QuerySet):
    """QuerySet optimizado para archivos de proyecto"""
    
    def with_related(self):
        """Incluye relaciones frecuentemente usadas"""
        return self.select_related(
            'phase',
            'phase__project', 
            'phase__project__organization',
            'uploaded_by'
        )
    
    def by_phase(self, phase_id):
        """Filtrar por fase con optimizaciones"""
        return self.filter(phase_id=phase_id)
    
    def by_organization(self, organization_id):
        """Filtrar por organización"""
        return self.filter(phase__project__organization_id=organization_id)
    
    def by_extension(self, extension):
        """Filtrar por extensión (case insensitive)"""
        return self.filter(ext_upper__iexact=extension.upper())
    
    def large_files(self, min_size_mb=10):
        """Archivos grandes (por defecto > 10MB)"""
        min_bytes = min_size_mb * 1024 * 1024
        return self.filter(size_bytes__gte=min_bytes)
    
    def recent(self, days=30):
        """Archivos recientes"""
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(uploaded_at__gte=cutoff)
    
    def with_checksums(self):
        """Solo archivos con checksum calculado"""
        return self.exclude(checksum_sha256='')
    
    def duplicates_by_checksum(self):
        """Encontrar archivos duplicados por checksum"""
        return self.exclude(checksum_sha256='').values('checksum_sha256').annotate(
            count=Count('id')
        ).filter(count__gt=1)


class ProjectFileManager(models.Manager):
    """Manager optimizado para ProjectFile"""
    
    def get_queryset(self):
        return ProjectFileQuerySet(self.model, using=self._db)
    
    def with_related(self):
        return self.get_queryset().with_related()
    
    def by_phase(self, phase_id):
        return self.get_queryset().by_phase(phase_id)
    
    def by_organization(self, organization_id):
        return self.get_queryset().by_organization(organization_id)
    
    def by_extension(self, extension):
        return self.get_queryset().by_extension(extension)
    
    def large_files(self, min_size_mb=10):
        return self.get_queryset().large_files(min_size_mb)
    
    def recent(self, days=30):
        return self.get_queryset().recent(days)
    
    def with_checksums(self):
        return self.get_queryset().with_checksums()
    
    def duplicates_by_checksum(self):
        return self.get_queryset().duplicates_by_checksum()
    
    def get_phase_stats(self, phase_id, use_cache=True):
        """
        Estadísticas optimizadas para una fase específica
        """
        cache_key = f"phase_file_stats_{phase_id}"
        
        if use_cache:
            stats = cache.get(cache_key)
            if stats:
                return stats
        
        # Calcular estadísticas
        files = self.by_phase(phase_id)
        stats = files.aggregate(
            total_files=Count('id'),
            total_size=Sum('size_bytes'),
            avg_size=models.Avg('size_bytes')
        )
        
        # Agregar estadísticas por tipo
        stats['by_extension'] = list(
            files.values('ext_upper')
            .annotate(count=Count('id'), size=Sum('size_bytes'))
            .order_by('-count')[:10]
        )
        
        # Archivos recientes (última semana)
        stats['recent_count'] = files.recent(7).count()
        
        # Caché por 10 minutos
        if use_cache:
            cache.set(cache_key, stats, 600)
        
        return stats
    
    def cleanup_orphaned_files(self, dry_run=True):
        """
        Identifica archivos huérfanos (sin archivo físico)
        """
        orphaned = []
        
        for file_obj in self.all():
            try:
                if not file_obj.file or not file_obj.file.storage.exists(file_obj.file.name):
                    orphaned.append(file_obj)
                    if not dry_run:
                        logger.warning(f"Deleting orphaned file record: {file_obj.id}")
                        file_obj.delete()
            except Exception as e:
                logger.error(f"Error checking file {file_obj.id}: {e}")
        
        return orphaned
    
    def get_storage_usage_by_org(self, organization_id):
        """
        Uso de almacenamiento por organización con caché
        """
        cache_key = f"org_storage_{organization_id}"
        usage = cache.get(cache_key)
        
        if not usage:
            usage = self.by_organization(organization_id).aggregate(
                total_files=Count('id'),
                total_size=Sum('size_bytes')
            )
            # Caché por 30 minutos
            cache.set(cache_key, usage, 1800)
        
        return usage
