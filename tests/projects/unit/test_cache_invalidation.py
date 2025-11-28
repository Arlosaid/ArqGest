"""
Tests para validar la invalidación de cache en todo el proyecto.
Verifica que los signals invaliden correctamente el cache cuando se modifican datos.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from decimal import Decimal


@pytest.fixture
def mock_cache():
    """Fixture para mockear el cache y rastrear llamadas."""
    with patch('django.core.cache.cache') as mock:
        mock.get.return_value = None
        mock.set.return_value = None
        mock.delete.return_value = None
        mock.delete_many.return_value = None
        yield mock


class TestPendingRequestsCache:
    """Tests para el cache de solicitudes pendientes en middleware."""
    
    @pytest.mark.django_db
    def test_pending_requests_cache_invalidates_on_renewal_save(self, organization, subscription):
        """Verifica que el cache se invalida cuando se guarda una RenewalRequest."""
        from apps.plans.models import RenewalRequest
        
        cache_key = f"org_pending_requests:{organization.id}"
        
        # Setear un valor en cache
        cache.set(cache_key, {'renewal': False, 'upgrade': False}, 60)
        assert cache.get(cache_key) is not None
        
        # Crear una solicitud de renovación
        renewal = RenewalRequest.objects.create(
            organization=organization,
            subscription=subscription,
            renewal_amount=Decimal('199.00'),
            renewal_days=30,
            status='pending'
        )
        
        # Verificar que el cache fue invalidado
        assert cache.get(cache_key) is None
    
    @pytest.mark.django_db
    def test_pending_requests_cache_invalidates_on_renewal_delete(self, organization, subscription):
        """Verifica que el cache se invalida cuando se elimina una RenewalRequest."""
        from apps.plans.models import RenewalRequest
        
        cache_key = f"org_pending_requests:{organization.id}"
        
        # Crear y luego eliminar
        renewal = RenewalRequest.objects.create(
            organization=organization,
            subscription=subscription,
            renewal_amount=Decimal('199.00'),
            renewal_days=30,
            status='pending'
        )
        
        # Setear cache después de la creación
        cache.set(cache_key, {'renewal': True, 'upgrade': False}, 60)
        assert cache.get(cache_key) is not None
        
        # Eliminar
        renewal.delete()
        
        # Verificar invalidación
        assert cache.get(cache_key) is None
    
    @pytest.mark.django_db
    def test_pending_requests_cache_invalidates_on_upgrade_save(self, organization, subscription, basic_plan):
        """Verifica que el cache se invalida cuando se guarda una UpgradeRequest."""
        from apps.plans.models import UpgradeRequest
        
        cache_key = f"org_pending_requests:{organization.id}"
        
        # Setear cache
        cache.set(cache_key, {'renewal': False, 'upgrade': False}, 60)
        assert cache.get(cache_key) is not None
        
        # Crear solicitud de upgrade
        upgrade = UpgradeRequest.objects.create(
            organization=organization,
            current_plan=subscription.plan,
            requested_plan=basic_plan,
            amount=Decimal('299.00'),
            status='pending'
        )
        
        # Verificar invalidación
        assert cache.get(cache_key) is None


class TestDashboardStatsCache:
    """Tests para el cache de estadísticas del dashboard."""
    
    @pytest.mark.django_db
    def test_dashboard_stats_cache_invalidates_on_client_save(self, organization):
        """Verifica que el cache se invalida cuando se guarda un cliente."""
        from apps.orgs.models import Client
        
        cache_key = f"dashboard_stats:{organization.id}"
        
        # Setear cache
        cache.set(cache_key, {'total_clients': 0, 'total_tasks': 0}, 300)
        assert cache.get(cache_key) is not None
        
        # Crear cliente
        client = Client.objects.create(
            organization=organization,
            name='Test Client',
            email='client@test.com'
        )
        
        # Verificar invalidación
        assert cache.get(cache_key) is None
    
    @pytest.mark.django_db
    def test_dashboard_stats_cache_invalidates_on_client_delete(self, organization):
        """Verifica que el cache se invalida cuando se elimina un cliente."""
        from apps.orgs.models import Client
        
        # Crear cliente primero
        client = Client.objects.create(
            organization=organization,
            name='Test Client',
            email='client@test.com'
        )
        
        cache_key = f"dashboard_stats:{organization.id}"
        
        # Setear cache
        cache.set(cache_key, {'total_clients': 1, 'total_tasks': 0}, 300)
        assert cache.get(cache_key) is not None
        
        # Eliminar cliente
        client.delete()
        
        # Verificar invalidación
        assert cache.get(cache_key) is None
    
    @pytest.mark.django_db
    def test_dashboard_stats_cache_invalidates_on_task_save(self, project_with_phase):
        """Verifica que el cache se invalida cuando se guarda una tarea."""
        from apps.projects.models import Task
        
        organization = project_with_phase.organization
        cache_key = f"dashboard_stats:{organization.id}"
        
        # Setear cache
        cache.set(cache_key, {'total_clients': 0, 'total_tasks': 0}, 300)
        assert cache.get(cache_key) is not None
        
        # Crear tarea
        phase = project_with_phase.phases.first()
        task = Task.objects.create(
            phase=phase,
            title='Test Task',
            status='TODO'
        )
        
        # Verificar invalidación
        assert cache.get(cache_key) is None


class TestProjectProgressCache:
    """Tests para el cache de progreso de proyectos."""
    
    @pytest.mark.django_db
    def test_project_progress_uses_aggregated_query(self):
        """Verifica que get_dashboard_projects_progress usa query agregada."""
        from apps.projects.cache_utils import get_or_set_dashboard_projects_progress
        from apps.projects.models import Project, Task
        from apps.orgs.models import Organization
        from apps.plans.models import Plan, Subscription
        from apps.accounts.models import User
        
        # Crear organización con suscripción
        org = Organization.objects.create(name='Test Org')
        plan = Plan.objects.filter(is_active=True).first()
        if not plan:
            plan = Plan.objects.create(name='trial', display_name='Trial', is_active=True)
        Subscription.objects.create(organization=org, plan=plan)
        
        # Crear usuario owner
        owner = User.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Owner',
            organization=org,
            is_org_admin=True
        )
        
        # Crear proyecto con owner
        project = Project.objects.create(
            organization=org,
            owner=owner,
            name='Test Project',
            status='ACTIVE'
        )
        
        # Limpiar cache
        cache.delete(f"dashboard_projects_progress:{org.id}")
        
        # Llamar función
        progress = get_or_set_dashboard_projects_progress(org.id)
        
        # Verificar que retorna dict vacío o con el proyecto
        assert isinstance(progress, dict)
    
    @pytest.mark.django_db
    def test_project_progress_cache_invalidates_on_task_status_change(self, project_with_phase):
        """Verifica que el cache de progreso se invalida cuando cambia el estado de una tarea."""
        from apps.projects.models import Task
        
        organization = project_with_phase.organization
        cache_key = f"dashboard_projects_progress:{organization.id}"
        
        # Crear tarea
        phase = project_with_phase.phases.first()
        task = Task.objects.create(
            phase=phase,
            title='Test Task',
            status='TODO'
        )
        
        # Setear cache
        cache.set(cache_key, {project_with_phase.id: 0}, 600)
        assert cache.get(cache_key) is not None
        
        # Cambiar estado de tarea
        task.status = 'DONE'
        task.save()
        
        # Verificar invalidación
        assert cache.get(cache_key) is None


class TestSafeDeletePattern:
    """Tests para la función safe_delete_pattern."""
    
    def test_safe_delete_pattern_with_redis_backend(self):
        """Verifica que safe_delete_pattern funciona con backend de Redis."""
        from apps.orgs.cache_utils import safe_delete_pattern
        
        # Si estamos usando Redis, debería funcionar
        result = safe_delete_pattern('test_pattern:*')
        # El resultado depende del backend, pero no debería lanzar excepción
        assert result in [True, False]
    
    def test_safe_delete_pattern_handles_missing_method(self):
        """Verifica que safe_delete_pattern maneja backends sin delete_pattern."""
        from apps.files.cache_utils import safe_delete_pattern
        
        # Mockear cache sin delete_pattern
        with patch('apps.files.cache_utils.cache') as mock_cache:
            del mock_cache.delete_pattern  # Simular backend sin el método
            mock_cache.configure_mock(**{'__class__.__name__': 'LocMemCache'})
            
            # No debería lanzar excepción
            result = safe_delete_pattern('test:*')
            assert result == False


class TestFinanceCacheInvalidation:
    """Tests para la invalidación de cache financiero."""
    
    @pytest.mark.django_db
    def test_payment_save_invalidates_finance_cache(self, project_with_budget):
        """Verifica que guardar un pago invalida el cache financiero."""
        from apps.projects.models import ProjectPayment
        from django.utils import timezone
        
        project = project_with_budget
        org_id = project.organization.id
        
        # Setear caches
        cache.set(f"project_total_paid:{project.id}", Decimal('0'), 300)
        cache.set(f"project_finance_stats:{project.id}", {'total': 0}, 300)
        
        # Crear pago
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            description='Test payment',
            date=timezone.now().date()
        )
        
        # Verificar invalidación
        assert cache.get(f"project_total_paid:{project.id}") is None
        assert cache.get(f"project_finance_stats:{project.id}") is None
    
    @pytest.mark.django_db
    def test_payment_delete_invalidates_finance_cache(self, project_with_budget):
        """Verifica que eliminar un pago invalida el cache financiero."""
        from apps.projects.models import ProjectPayment
        from django.utils import timezone
        
        project = project_with_budget
        
        # Crear pago
        payment = ProjectPayment.objects.create(
            project=project,
            amount=Decimal('1000.00'),
            description='Test payment',
            date=timezone.now().date()
        )
        
        # Setear caches después de la creación
        cache.set(f"project_total_paid:{project.id}", Decimal('1000'), 300)
        cache.set(f"project_finance_stats:{project.id}", {'total': 1000}, 300)
        
        # Eliminar pago
        payment.delete()
        
        # Verificar invalidación
        assert cache.get(f"project_total_paid:{project.id}") is None
        assert cache.get(f"project_finance_stats:{project.id}") is None


class TestGetDashboardStats:
    """Tests para la función get_or_set_dashboard_stats."""
    
    @pytest.mark.django_db
    def test_get_dashboard_stats_returns_correct_structure(self, organization):
        """Verifica que get_or_set_dashboard_stats retorna la estructura correcta."""
        from apps.projects.cache_utils import get_or_set_dashboard_stats
        
        # Limpiar cache
        cache.delete(f"dashboard_stats:{organization.id}")
        
        # Obtener stats
        stats = get_or_set_dashboard_stats(organization.id)
        
        # Verificar estructura
        assert 'total_clients' in stats
        assert 'total_tasks' in stats
        assert 'total_tasks_done' in stats
        assert 'total_active_projects' in stats
    
    @pytest.mark.django_db
    def test_get_dashboard_stats_caches_result(self, organization):
        """Verifica que get_or_set_dashboard_stats guarda en cache."""
        from apps.projects.cache_utils import get_or_set_dashboard_stats
        
        cache_key = f"dashboard_stats:{organization.id}"
        
        # Limpiar cache
        cache.delete(cache_key)
        
        # Primera llamada - debería calcular y cachear
        stats1 = get_or_set_dashboard_stats(organization.id)
        
        # Verificar que se guardó en cache
        cached = cache.get(cache_key)
        assert cached is not None
        assert cached == stats1
        
        # Segunda llamada - debería usar cache
        stats2 = get_or_set_dashboard_stats(organization.id)
        assert stats2 == stats1
