"""
Tests para validación de storage disponible ANTES del upload.

Estos tests verifican:
1. Context processor inyecta STORAGE_INFO correctamente
2. Endpoint API /api/storage-availability/ funciona
3. Validación frontend bloquea archivos antes de subir
"""
import pytest
import json
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import RequestFactory, Client
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.core.cache import cache

from apps.orgs.storage_service import StorageService
from apps.orgs.models import Organization
from apps.plans.models import Plan
from apps.accounts.models import User
from apps.projects.models import Project, Phase
from apps.files.models import ProjectFile
from core.context_processors import global_settings
from tests.factories.orgs import OrganizationFactory
from tests.factories.accounts import UserFactory
from tests.factories.plans import PlanFactory, BasicPlanFactory, SubscriptionFactory
from tests.factories.projects import ProjectFactory, PhaseFactory
from tests.factories.files.file_factories import ProjectFileFactory, LargeFileFactory


@pytest.fixture(autouse=True)
def clear_cache():
    """Limpiar cache antes de cada test"""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
@pytest.mark.unit
class TestContextProcessorStorageInfo:
    """Tests del context processor que inyecta STORAGE_INFO"""
    
    def test_storage_info_injected_for_authenticated_user_with_org(self, use_local_storage):
        """STORAGE_INFO se inyecta para usuarios autenticados con organización"""
        # Setup
        plan = PlanFactory(max_storage_gb=10)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Crear request mock
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        
        # Ejecutar context processor
        context = global_settings(request)
        
        # Verificar
        assert 'STORAGE_INFO' in context
        assert context['STORAGE_INFO'] is not None
        assert 'available_bytes' in context['STORAGE_INFO']
        assert 'used_gb' in context['STORAGE_INFO']
        assert 'limit_gb' in context['STORAGE_INFO']
        assert 'remaining_gb' in context['STORAGE_INFO']
        assert 'usage_percentage' in context['STORAGE_INFO']
        assert 'status' in context['STORAGE_INFO']
    
    def test_storage_info_none_for_anonymous_user(self, use_local_storage):
        """STORAGE_INFO es None para usuarios anónimos"""
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        context = global_settings(request)
        
        assert 'STORAGE_INFO' in context
        assert context['STORAGE_INFO'] is None
    
    def test_storage_info_calculates_available_bytes_correctly(self, use_local_storage):
        """available_bytes se calcula correctamente a partir de remaining_gb"""
        plan = PlanFactory(max_storage_gb=5)  # 5 GB límite
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Crear archivo de 1GB
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=1 * 1024 * 1024 * 1024  # 1 GB
        )
        
        cache.clear()
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        
        context = global_settings(request)
        
        # Debería tener ~4GB disponibles (5GB - 1GB usado)
        assert context['STORAGE_INFO'] is not None
        available_gb = context['STORAGE_INFO']['available_bytes'] / (1024 ** 3)
        assert 3.9 <= available_gb <= 4.1  # Tolerancia para redondeo
    
    def test_storage_info_reflects_usage_status(self, use_local_storage):
        """El status refleja correctamente el nivel de uso"""
        plan = PlanFactory(max_storage_gb=1)  # 1 GB límite
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Crear archivo que use 95% del espacio
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=int(0.95 * 1024 * 1024 * 1024)  # 0.95 GB
        )
        
        cache.clear()
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        
        context = global_settings(request)
        
        assert context['STORAGE_INFO']['status'] == 'critical'
        assert context['STORAGE_INFO']['usage_percentage'] >= 90


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageAvailabilityAPI:
    """Tests del endpoint API /api/storage-availability/"""
    
    def test_api_returns_storage_info_for_authenticated_user(self, use_local_storage, client):
        """API retorna info de storage para usuario autenticado"""
        plan = PlanFactory(max_storage_gb=10)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar force_login en lugar de login para evitar problema con Axes
        client.force_login(user)
        
        response = client.get('/api/storage-availability/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'available_bytes' in data['data']
        assert 'used_gb' in data['data']
        assert 'limit_gb' in data['data']
        assert 'remaining_gb' in data['data']
        assert 'usage_percentage' in data['data']
        assert 'status' in data['data']
    
    def test_api_requires_authentication(self, use_local_storage, client):
        """API requiere autenticación"""
        response = client.get('/api/storage-availability/')
        
        # Debería redirigir a login (302) o retornar 403
        assert response.status_code in [302, 403]
    
    def test_api_returns_correct_values_after_file_upload(self, use_local_storage, client):
        """API retorna valores actualizados después de subir archivo"""
        plan = PlanFactory(max_storage_gb=5)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar force_login en lugar de login
        client.force_login(user)
        
        # Primera llamada - sin archivos
        response1 = client.get('/api/storage-availability/')
        data1 = response1.json()
        
        initial_available = data1['data']['available_bytes']
        
        # Simular upload de archivo
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        file_size = 500 * 1024 * 1024  # 500 MB
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=file_size
        )
        
        # Invalidar cache
        StorageService.invalidate_cache(org.id)
        
        # Segunda llamada - después del upload
        response2 = client.get('/api/storage-availability/')
        data2 = response2.json()
        
        new_available = data2['data']['available_bytes']
        
        # El espacio disponible debe haber disminuido
        assert new_available < initial_available
        assert (initial_available - new_available) >= (file_size * 0.99)  # Tolerancia del 1%
    
    def test_api_returns_file_count(self, use_local_storage, client):
        """API incluye conteo de archivos"""
        plan = PlanFactory(max_storage_gb=10)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Crear 3 archivos
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        for i in range(3):
            ProjectFileFactory(phase=phase, uploaded_by=user, size_bytes=1024)
        
        cache.clear()
        
        # Usar force_login en lugar de login
        client.force_login(user)
        
        response = client.get('/api/storage-availability/')
        data = response.json()
        
        assert data['data']['file_count'] == 3


@pytest.mark.django_db
@pytest.mark.unit
class TestPreUploadStorageValidation:
    """Tests de validación de storage ANTES del upload"""
    
    def test_can_upload_returns_false_when_no_space(self, use_local_storage):
        """can_upload_file retorna False cuando no hay espacio suficiente"""
        plan = PlanFactory(max_storage_gb=1)  # 1 GB
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar 0.9 GB
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=int(0.9 * 1024 * 1024 * 1024)
        )
        
        cache.clear()
        
        # Intentar subir 500 MB más (no debería caber)
        file_size = 500 * 1024 * 1024
        can_upload, error, data = StorageService.can_upload_file(org, file_size)
        
        assert can_upload is False
        assert error is not None
        assert 'no se puede subir' in error.lower() or 'no tienes' in error.lower()
    
    def test_can_upload_returns_true_when_space_available(self, use_local_storage):
        """can_upload_file retorna True cuando hay espacio suficiente"""
        plan = PlanFactory(max_storage_gb=10)  # 10 GB
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        cache.clear()
        
        # Intentar subir 500 MB
        file_size = 500 * 1024 * 1024
        can_upload, error, data = StorageService.can_upload_file(org, file_size)
        
        assert can_upload is True
        assert error == ""
    
    def test_frontend_gets_correct_available_bytes(self, use_local_storage, client):
        """Frontend recibe bytes disponibles correctos para validación"""
        plan = PlanFactory(max_storage_gb=2)  # 2 GB
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar 1.5 GB
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=int(1.5 * 1024 * 1024 * 1024)
        )
        
        cache.clear()
        
        # Usar force_login en lugar de login
        client.force_login(user)
        
        response = client.get('/api/storage-availability/')
        data = response.json()
        
        available_bytes = data['data']['available_bytes']
        available_mb = available_bytes / (1024 * 1024)
        
        # Debería tener ~500 MB disponibles (2GB - 1.5GB)
        assert 400 <= available_mb <= 600  # Tolerancia
        
        # Verificar que coincida con can_upload_file
        can_upload_600mb, _, _ = StorageService.can_upload_file(org, 600 * 1024 * 1024)
        can_upload_400mb, _, _ = StorageService.can_upload_file(org, 400 * 1024 * 1024)
        
        assert can_upload_400mb is True  # 400MB debe caber
        assert can_upload_600mb is False  # 600MB no debe caber


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageIndicatorData:
    """Tests de datos para el indicador visual de storage"""
    
    def test_storage_status_normal_under_75_percent(self, use_local_storage):
        """Status es 'normal' cuando el uso es menor al 75%"""
        plan = PlanFactory(max_storage_gb=10)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar 50%
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=int(5 * 1024 * 1024 * 1024)  # 5 GB de 10
        )
        
        cache.clear()
        
        summary = StorageService.get_storage_summary(org)
        assert summary['status'] == 'normal'
    
    def test_storage_status_warning_between_75_and_90_percent(self, use_local_storage):
        """Status es 'warning' cuando el uso está entre 75% y 90%"""
        plan = PlanFactory(max_storage_gb=10)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar 80%
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=int(8 * 1024 * 1024 * 1024)  # 8 GB de 10
        )
        
        cache.clear()
        
        summary = StorageService.get_storage_summary(org)
        assert summary['status'] == 'warning'
    
    def test_storage_status_critical_above_90_percent(self, use_local_storage):
        """Status es 'critical' cuando el uso es mayor al 90%"""
        plan = PlanFactory(max_storage_gb=10)
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org, plan=plan)
        user = UserFactory(organization=org)
        
        # Usar 95%
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        ProjectFileFactory(
            phase=phase,
            uploaded_by=user,
            size_bytes=int(9.5 * 1024 * 1024 * 1024)  # 9.5 GB de 10
        )
        
        cache.clear()
        
        summary = StorageService.get_storage_summary(org)
        assert summary['status'] == 'critical'
