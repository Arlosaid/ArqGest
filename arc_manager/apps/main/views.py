from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

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

    # Redirigir si la suscripción de la organización está expirada
    subscription = getattr(organization, 'subscription', None)
    if subscription and subscription.is_expired:
        return redirect(reverse('plans:subscription_dashboard'))

    # --- Widgets de Métricas para el Arquitecto ---

    # --- Consultas optimizadas con agregaciones ---
    
    # Obtener contadores en una sola consulta usando agregación
    from django.db.models import Count, Q
    
    # Contar proyectos y clientes de la organización
    org_stats = organization.__dict__
    total_projects = Project.objects.filter(organization=organization).count()
    total_clients = Client.objects.filter(organization=organization).count()
    
    # 1. Widget "Mis Tareas" - optimizado con select_related
    my_tasks = Task.objects.filter(
        assigned_to=current_user
    ).exclude(status='DONE').select_related(
        'phase__project', 
        'assigned_to'
    ).order_by('due_date')[:3]
    
    # Contar mis tareas pendientes (reutilizando filtro base)
    total_my_tasks = Task.objects.filter(
        assigned_to=current_user
    ).exclude(status='DONE').count()

    # 2. Widget "Proyectos Activos" - optimizado con prefetch
    active_projects = Project.objects.filter(
        organization=organization,
        status='ACTIVE'
    ).select_related('client').prefetch_related(
        'phases',
        'phases__tasks'
    ).order_by('-created_at')[:6]

    # 3. Widget "Archivos Recientes" - optimizado
    recent_files = ProjectFile.objects.filter(
        phase__project__organization=organization
    ).select_related(
        'phase__project',
        'uploaded_by'
    ).order_by('-uploaded_at')[:5]
    
    # Total de tareas de la organización (optimizado)
    total_tasks = Task.objects.filter(
        phase__project__organization=organization
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

        # Contadores totales para el dashboard
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'total_my_tasks': total_my_tasks,

        # Archivos recientes
        'recent_files': recent_files,

        # Para consistencia con la plantilla actual
        'tasks': my_tasks, 
    }
    
    return render(request, 'dashboard.html', context)
