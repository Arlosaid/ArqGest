from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache

from apps.projects.models import Project, Task
from apps.orgs.models import Client
from apps.files.models import ProjectFile

User = get_user_model()

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def dashboard(request):
    """
    Vista del dashboard principal enfocada en la experiencia del arquitecto.
    Muestra información relevante y accionable para el usuario actual.
    """
    current_user = request.user
    organization = getattr(current_user, 'organization', None)

    if not organization:
        # Si por alguna razón el usuario no tiene una organización,
        # podríamos redirigirlo a una página de error o de "espera".
        return render(request, 'error_page.html', {'message': 'No estás asociado a ninguna organización.'})

    # Obtener suscripción y flag de expiración (no redirigir: mostrar dashboard en modo lectura)
    subscription = getattr(organization, 'subscription', None)
    is_subscription_expired = bool(subscription and subscription.is_expired)

    # --- Widgets de Métricas para el Arquitecto ---

    # --- Consultas optimizadas con agregaciones y cache ---
    
    # Obtener contadores con cache (10 minutos)
    from django.db.models import Count, Q
    
    cache_key = f"dashboard_stats:{organization.id}:user:{current_user.id}"
    dashboard_stats = cache.get(cache_key)
    
    if dashboard_stats is None:
        # SEGURIDAD: Contar proyectos según permisos del usuario
        if current_user.is_org_admin:
            # Admins ven todos los proyectos (excluir archivados)
            total_projects = Project.objects.filter(
                organization=organization
            ).exclude(status='ARCHIVED').count()
        else:
            # Usuarios normales solo cuentan proyectos accesibles
            from apps.projects.cache_utils import get_or_set_user_accessible_projects
            
            accessible_data = get_or_set_user_accessible_projects(
                current_user.id,
                organization.id,
                is_admin=False
            )
            
            # Combinar IDs accesibles (activos + completados, sin archivados)
            all_accessible_ids = accessible_data['active_ids'] | accessible_data['completed_ids']
            total_projects = len(all_accessible_ids)
        
        total_clients = Client.objects.filter(organization=organization).count()
        
        dashboard_stats = {
            'total_projects': total_projects,
            'total_clients': total_clients,
        }
        # Cache por 10 minutos
        cache.set(cache_key, dashboard_stats, 600)
    else:
        total_projects = dashboard_stats['total_projects']
        total_clients = dashboard_stats['total_clients']
    
    # 1. Widget "Mis Tareas" - optimizado con select_related (excluir archivados)
    my_tasks = Task.objects.filter(
        assigned_to=current_user
    ).exclude(
        status='DONE'
    ).exclude(
        phase__project__status='ARCHIVED'
    ).select_related(
        'phase__project', 
        'assigned_to'
    ).order_by('due_date')[:3]
    
    # Contar mis tareas pendientes (reutilizando filtro base, excluir archivados)
    total_my_tasks = Task.objects.filter(
        assigned_to=current_user
    ).exclude(
        status='DONE'
    ).exclude(
        phase__project__status='ARCHIVED'
    ).count()

    # 2. Widget "Proyectos Activos" - optimizado con cache de progreso
    # SEGURIDAD: Filtrar proyectos según permisos del usuario
    if current_user.is_org_admin:
        # Admins ven todos los proyectos activos
        active_projects = Project.objects.filter(
            organization=organization,
            status='ACTIVE'
        ).select_related('client').order_by('-created_at')[:6]
    else:
        # Usuarios normales solo ven proyectos donde están asignados
        from apps.projects.cache_utils import get_or_set_user_accessible_projects
        
        accessible_data = get_or_set_user_accessible_projects(
            current_user.id,
            organization.id,
            is_admin=False
        )
        
        # Solo mostrar proyectos activos accesibles
        active_projects = Project.objects.filter(
            id__in=accessible_data['active_ids'],
            organization=organization
        ).select_related('client').order_by('-created_at')[:6]
    
    # Obtener progreso desde cache para todos los proyectos del dashboard
    if active_projects:
        from apps.projects.cache_utils import get_or_set_dashboard_projects_progress
        projects_progress = get_or_set_dashboard_projects_progress(organization.id)
        
        # Asignar progreso desde cache a cada proyecto
        for project in active_projects:
            project._cached_progress = projects_progress.get(project.id, 0)

    # 3. Widget "Archivos Recientes" - optimizado (excluir archivados)
    recent_files = ProjectFile.objects.filter(
        phase__project__organization=organization
    ).exclude(
        phase__project__status='ARCHIVED'
    ).select_related(
        'phase__project',
        'uploaded_by'
    ).order_by('-uploaded_at')[:5]
    
    # 4. Widget "Almacenamiento" - usando servicio optimizado con cache
    from apps.orgs.storage_service import StorageService
    storage_summary = StorageService.get_storage_summary(organization)
    
    # Total de tareas de la organización (optimizado, excluir archivados)
    total_tasks = Task.objects.filter(
        phase__project__organization=organization
    ).exclude(
        phase__project__status='ARCHIVED'
    ).count()
    
    # No necesitamos recent_clients ya que no se usa en el template

    context = {
        'user': current_user,
        'organization': organization,
        'greeting_name': current_user.first_name or current_user.email,

        # Datos para los widgets
        'my_tasks': my_tasks,
        'active_projects': active_projects,
        'total_clients': total_clients,
        'storage_summary': storage_summary,

        # Contadores totales para el dashboard
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'total_my_tasks': total_my_tasks,

        # Archivos recientes
        'recent_files': recent_files,

        # Para consistencia con la plantilla actual
        'tasks': my_tasks, 
        'is_subscription_expired': is_subscription_expired,
    }
    
    return render(request, 'dashboard.html', context)
