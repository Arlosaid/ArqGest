"""
Tests de almacenamiento y límites de storage

Validan:
- Límites de storage por organización
- Cálculos de uso
- Integración con StorageService
- Validaciones de cuotas
"""
import pytest
from django.core.cache import cache
from apps.files.models import ProjectFile
from apps.orgs.storage_service import StorageService
from tests.factories import (
    ProjectFileFactory,
    PDFFileFactory,
    LargeFileFactory,
    OrganizationFactory,
    SubscriptionFactory,
    BasicPlanFactory,
    PhaseFactory,
)


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageServiceCalculation:
    """Tests de cálculo de uso de storage"""
    
    def test_calculate_storage_for_org_with_files(self, use_local_storage):
        """Calcular uso de storage para org con archivos"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        # Crear archivos con tamaños conocidos
        PDFFileFactory(
            phase__project__organization=org,
            size_bytes=1024 * 1024  # 1MB
        )
        PDFFileFactory(
            phase__project__organization=org,
            size_bytes=2 * 1024 * 1024  # 2MB
        )
        
        # Limpiar cache para forzar cálculo
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['total_bytes'] == 3 * 1024 * 1024  # 3MB
        assert storage_data['file_count'] == 2
        assert 'total_gb' in storage_data
        assert 'plan_limit_gb' in storage_data
        assert 'usage_percentage' in storage_data
    
    def test_calculate_storage_for_empty_org(self, use_local_storage):
        """Calcular uso de storage para org sin archivos"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['total_bytes'] == 0
        assert storage_data['total_gb'] == 0
        assert storage_data['file_count'] == 0
    
    def test_calculate_storage_converts_to_gb_correctly(self, use_local_storage):
        """Conversión de bytes a GB es correcta"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        # 1 GB exacto
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['total_gb'] == 1.0


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageServiceCache:
    """Tests de caché de StorageService"""
    
    def test_cache_key_is_unique_per_org(self, use_local_storage):
        """Cada organización tiene su propia cache key"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        key1 = StorageService.get_cache_key(org1.id)
        key2 = StorageService.get_cache_key(org2.id)
        
        assert key1 != key2
        assert f"org_storage:{org1.id}" == key1
        assert f"org_storage:{org2.id}" == key2


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageLimits:
    """Tests de límites de storage"""
    
    def test_can_upload_returns_true_within_limit(self, use_local_storage):
        """can_upload retorna True si hay espacio disponible"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=10)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 1GB de 10GB disponibles
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=1 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        # Intentar subir 2GB más (debería ser permitido)
        can_upload, error, data = StorageService.can_upload_file(
            org,
            2 * 1024 * 1024 * 1024
        )
        
        assert can_upload is True
        # error puede ser None o string vacío
        assert not error
    
    def test_can_upload_returns_false_when_exceeds_limit(self, use_local_storage):
        """can_upload retorna False si excede el límite"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=5)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 4GB de 5GB disponibles
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=4 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        # Intentar subir 2GB más (debería ser rechazado)
        can_upload, error, data = StorageService.can_upload_file(
            org,
            2 * 1024 * 1024 * 1024
        )
        
        assert can_upload is False
        assert error is not None
    
    def test_storage_limit_includes_extra_storage(self, use_local_storage):
        """Límite de storage incluye extra_storage_gb"""
        org = OrganizationFactory(extra_storage_gb=5)
        plan = BasicPlanFactory(max_storage_gb=10)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        # Límite total = plan (10GB) + extra (5GB) = 15GB
        assert storage_data['plan_limit_gb'] == 15
    
    def test_storage_limit_handles_negative_extra_storage(self, use_local_storage):
        """
        Límite de storage maneja extra_storage_gb negativo.
        
        BUG POTENCIAL: extra_storage_gb negativo no debería dar límite negativo.
        """
        org = OrganizationFactory(extra_storage_gb=-20)
        plan = BasicPlanFactory(max_storage_gb=10)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        total_limit = org.get_total_storage_limit_gb()
        
        # No debe ser negativo
        assert total_limit >= 0


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageUsagePercentage:
    """Tests de cálculo de porcentaje de uso"""
    
    def test_usage_percentage_at_zero(self, use_local_storage):
        """Porcentaje de uso es 0% sin archivos"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['usage_percentage'] == 0
    
    def test_usage_percentage_at_half(self, use_local_storage):
        """Porcentaje de uso es correcto al 50%"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=10)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 5GB de 10GB
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=5 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['usage_percentage'] == 50.0
    
    def test_usage_percentage_caps_at_100(self, use_local_storage):
        """Porcentaje de uso se limita a 100%"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=5)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 10GB de 5GB (200%)
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=10 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        # Debe mostrar máximo 100%
        assert storage_data['usage_percentage'] == 100


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageRemainingSpace:
    """Tests de cálculo de espacio restante"""
    
    def test_remaining_gb_is_calculated_correctly(self, use_local_storage):
        """Espacio restante se calcula correctamente"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=10)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 3GB
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=3 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        # Deben quedar 7GB
        assert storage_data['remaining_gb'] == 7.0
    
    def test_remaining_gb_never_negative(self, use_local_storage):
        """Espacio restante nunca es negativo"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=5)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 10GB (excede límite)
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=10 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        # No debe ser negativo
        assert storage_data['remaining_gb'] >= 0


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageOverLimitFlag:
    """Tests del flag is_over_limit"""
    
    def test_is_over_limit_false_within_quota(self, use_local_storage):
        """is_over_limit es False dentro del límite"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=10)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 5GB de 10GB
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=5 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['is_over_limit'] is False
    
    def test_is_over_limit_true_when_exceeded(self, use_local_storage):
        """is_over_limit es True cuando se excede"""
        org = OrganizationFactory()
        plan = BasicPlanFactory(max_storage_gb=5)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        # Usar 6GB de 5GB
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=6 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['is_over_limit'] is True


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageFileCount:
    """Tests de conteo de archivos"""
    
    def test_file_count_is_accurate(self, use_local_storage):
        """Conteo de archivos es preciso"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        PDFFileFactory(phase__project__organization=org)
        PDFFileFactory(phase__project__organization=org)
        PDFFileFactory(phase__project__organization=org)
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['file_count'] == 3
    
    def test_file_count_only_for_org(self, use_local_storage):
        """Conteo solo incluye archivos de la organización"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        plan1 = BasicPlanFactory(name="Plan Org 1")
        plan2 = BasicPlanFactory(name="Plan Org 2")
        
        subscription1 = SubscriptionFactory(organization=org1, plan=plan1)
        subscription2 = SubscriptionFactory(organization=org2, plan=plan2)
        
        PDFFileFactory(phase__project__organization=org1)
        PDFFileFactory(phase__project__organization=org1)
        PDFFileFactory(phase__project__organization=org2)
        
        cache.clear()
        
        storage_org1 = StorageService.calculate_storage_usage(org1)
        
        assert storage_org1['file_count'] == 2


@pytest.mark.django_db
@pytest.mark.unit
class TestStorageEdgeCases:
    """Tests de edge cases de storage"""
    
    def test_org_without_subscription_has_fallback_limit(self, use_local_storage):
        """Organización sin suscripción tiene límite por defecto"""
        org = OrganizationFactory()
        # No crear suscripción
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        # Debe tener límite por defecto (10GB según el código)
        assert storage_data['plan_limit_gb'] >= 0
    
    def test_org_with_zero_limit(self, use_local_storage):
        """Organización con límite de 0GB"""
        org = OrganizationFactory(extra_storage_gb=-100)
        plan = BasicPlanFactory(max_storage_gb=0)
        subscription = SubscriptionFactory(organization=org, plan=plan)
        
        total_limit = org.get_total_storage_limit_gb()
        
        # No debe ser negativo
        assert total_limit >= 0
    
    def test_storage_with_very_small_file(self, use_local_storage):
        """Storage con archivo muy pequeño (1 byte)"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        PDFFileFactory(
            phase__project__organization=org,
            size_bytes=1
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['total_bytes'] == 1
        assert storage_data['total_gb'] < 0.01
    
    def test_storage_with_very_large_file(self, use_local_storage):
        """Storage con archivo muy grande (1TB)"""
        org = OrganizationFactory()
        subscription = SubscriptionFactory(organization=org)
        
        # 1TB = 1024GB
        LargeFileFactory(
            phase__project__organization=org,
            size_bytes=1024 * 1024 * 1024 * 1024
        )
        
        cache.clear()
        
        storage_data = StorageService.calculate_storage_usage(org)
        
        assert storage_data['total_gb'] == 1024.0


