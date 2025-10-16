"""
Módulo de caché específico para optimización del módulo de finanzas.
Implementa estrategias de caché con Redis para mejorar el rendimiento.
"""
from django.core.cache import cache
from django.db.models import Sum, Count, Q, Max
from django.conf import settings
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Timeouts de caché específicos para finanzas
FINANCE_CACHE_TIMEOUT = 60 * 15  # 15 minutos
PROJECT_STATS_TIMEOUT = 60 * 30  # 30 minutos
PAYMENT_STATS_TIMEOUT = 60 * 10  # 10 minutos

def get_organization_finance_stats(organization_id, force_refresh=False):
    """
    Obtiene estadísticas financieras de la organización desde caché.
    Optimización crítica para el dashboard de finanzas.
    """
    cache_key = f"org_finance_stats:{organization_id}"
    
    if not force_refresh:
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return cached_stats
    
    from apps.projects.models import Project
    
    # Consulta optimizada con agregaciones en BD
    active_projects = Project.objects.filter(
        organization_id=organization_id,
        status='ACTIVE'
    ).select_related('client', 'owner').prefetch_related('payments')
    
    # Estadísticas generales
    total_projects = Project.objects.filter(organization_id=organization_id).count()
    configured_projects = Project.objects.filter(
        organization_id=organization_id,
        budget_configured=True
    ).count()
    
    # Estadísticas financieras con agregaciones optimizadas
    finance_aggregates = active_projects.aggregate(
        total_budget=Sum('total_budget'),
        active_configured_count=Count('id', filter=Q(budget_configured=True))
    )
    
    # Calcular total_paid con una sola consulta agregada
    from apps.projects.models import ProjectPayment
    total_paid_result = ProjectPayment.objects.filter(
        project__organization_id=organization_id,
        project__status='ACTIVE'
    ).aggregate(total_paid=Sum('amount'))
    
    total_budget = finance_aggregates['total_budget'] or Decimal('0.00')
    total_paid = total_paid_result['total_paid'] or Decimal('0.00')
    active_configured = finance_aggregates['active_configured_count'] or 0
    
    stats = {
        'total_projects': total_projects,
        'configured_projects': configured_projects,
        'pending_configuration': total_projects - configured_projects,
        'active_configured': active_configured,
        'total_budget': float(total_budget),
        'total_paid': float(total_paid),
        'pending_amount': float(total_budget - total_paid) if total_budget > 0 else 0,
        'overall_percentage': int((total_paid / total_budget * 100)) if total_budget > 0 else 0,
    }
    
    # Guardar en caché
    cache.set(cache_key, stats, FINANCE_CACHE_TIMEOUT)
    
    logger.info(f"Finance stats cached for organization {organization_id}")
    return stats

def get_project_finance_stats(project_id, force_refresh=False):
    """
    Obtiene estadísticas financieras de un proyecto específico.
    Optimización para vistas de detalle de proyecto.
    """
    cache_key = f"project_finance_stats:{project_id}"
    
    if not force_refresh:
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return cached_stats
    
    from apps.projects.models import Project, ProjectPayment
    
    try:
        project = Project.objects.select_related('client', 'owner').get(id=project_id)
        
        # Calcular total_paid con agregación optimizada
        total_paid_result = ProjectPayment.objects.filter(
            project_id=project_id
        ).aggregate(total_paid=Sum('amount'))
        
        total_paid = total_paid_result['total_paid'] or Decimal('0.00')
        total_budget = project.total_budget or Decimal('0.00')
        
        stats = {
            'total_budget': float(total_budget),
            'total_paid': float(total_paid),
            'remaining_amount': float(total_budget - total_paid) if total_budget > 0 else 0,
            'payment_percentage': int((total_paid / total_budget * 100)) if total_budget > 0 else 0,
            'budget_configured': project.budget_configured,
            'payment_status': project.payment_status,
        }
        
        # Guardar en caché
        cache.set(cache_key, stats, PROJECT_STATS_TIMEOUT)
        
        return stats
        
    except Project.DoesNotExist:
        return None

def get_cached_projects_with_finance(organization_id, limit=8, offset=0):
    """
    Obtiene proyectos con estadísticas financieras desde caché.
    Optimización para listados paginados.
    """
    cache_key = f"projects_finance_list:{organization_id}:{limit}:{offset}"
    
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    from apps.projects.models import Project
    
    # Consulta optimizada con prefetch
    projects = Project.objects.filter(
        organization_id=organization_id
    ).select_related('client', 'owner').prefetch_related('payments')[
        offset:offset + limit
    ]
    
    # Calcular estadísticas para cada proyecto
    projects_data = []
    for project in projects:
        project_stats = get_project_finance_stats(project.id)
        if project_stats:
            projects_data.append({
                'project': project,
                'stats': project_stats
            })
    
    # Guardar en caché por 10 minutos
    cache.set(cache_key, projects_data, 600)
    
    return projects_data

def invalidate_finance_cache(organization_id=None, project_id=None):
    """
    Invalida caché financiero cuando se realizan cambios.
    Debe llamarse después de crear/editar/eliminar pagos o presupuestos.
    """
    patterns_to_delete = []
    
    if organization_id:
        patterns_to_delete.extend([
            f"org_finance_stats:{organization_id}",
            f"projects_finance_list:{organization_id}:*",
        ])
    
    if project_id:
        patterns_to_delete.extend([
            f"project_finance_stats:{project_id}",
        ])
    
    # Eliminar patrones de caché
    for pattern in patterns_to_delete:
        try:
            cache.delete_pattern(pattern)
            logger.info(f"Deleted cache pattern: {pattern}")
        except Exception as e:
            logger.warning(f"Could not delete cache pattern {pattern}: {e}")

def cache_payment_aggregates(project_id):
    """
    Pre-cachea agregaciones de pagos para un proyecto.
    Útil para proyectos con muchos pagos.
    """
    cache_key = f"payment_aggregates:{project_id}"
    
    from apps.projects.models import ProjectPayment
    
    aggregates = ProjectPayment.objects.filter(project_id=project_id).aggregate(
        total_paid=Sum('amount'),
        payment_count=Count('id'),
        latest_payment_date=Max('date')
    )
    
    cache.set(cache_key, aggregates, PAYMENT_STATS_TIMEOUT)
    return aggregates

# Decorador para cachear métodos de modelo
def cache_model_property(timeout=300):
    """
    Decorador para cachear propiedades costosas de modelos.
    """
    def decorator(func):
        def wrapper(self):
            cache_key = f"model_property:{self.__class__.__name__}:{self.id}:{func.__name__}"
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            result = func(self)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator
