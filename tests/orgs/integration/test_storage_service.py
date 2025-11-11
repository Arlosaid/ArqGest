"""
Tests de integración para StorageService

Tests robustos que verifican el funcionamiento completo del sistema de almacenamiento,
incluyendo cálculos, cache, y detección de bugs reales.
"""
import pytest
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
from unittest.mock import patch, Mock, MagicMock
from tests.factories import (
    OrganizationFactory,
    OrganizationWithExtraStorageFactory,
)
from apps.orgs.storage_service import StorageService


# ============================================================================
# TESTS DE CÁLCULO DE ALMACENAMIENTO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestStorageServiceCalculations:
    """Tests de cálculo de uso de almacenamiento"""
    
    def test_calculate_storage_empty_organization(self):
        """Organización sin archivos debe retornar 0 GB"""
        org = OrganizationFactory()
        
        result = StorageService.calculate_storage_usage(org)
        
        assert result['total_gb'] == 0
        assert result['total_bytes'] == 0
        assert result['file_count'] == 0
        assert result['is_over_limit'] is False
    
    def test_calculate_storage_with_fallback_plan_limit(self):
        """Sin subscription debe usar fallback de 10 GB"""
        org = OrganizationFactory()
        
        result = StorageService.calculate_storage_usage(org)
        
        assert result['plan_limit_gb'] == 10
    
    def test_calculate_storage_with_extra_storage(self):
        """Límite debe incluir almacenamiento extra"""
        org = OrganizationWithExtraStorageFactory(extra_storage_gb=50)
        
        result = StorageService.calculate_storage_usage(org)
        
        # 10 (fallback) + 50 (extra) = 60
        assert result['plan_limit_gb'] == 60
    
    def test_calculate_storage_usage_percentage_empty(self):
        """Porcentaje debe ser 0 si no hay uso"""
        org = OrganizationFactory()
        
        result = StorageService.calculate_storage_usage(org)
        
        assert result['usage_percentage'] == 0
    
    def test_calculate_storage_remaining_gb(self):
        """Remaining GB debe calcularse correctamente"""
        org = OrganizationFactory()  # 10 GB limit
        
        result = StorageService.calculate_storage_usage(org)
        
        # Sin uso: remaining = limit
        assert result['remaining_gb'] == 10
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_with_files(self, mock_project_file):
        """
        Calcular almacenamiento con archivos mockeados
        """
        org = OrganizationFactory()
        
        # Mock queryset para simular 10 GB (10 * 1024^3 bytes)
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 10 * 1024**3}
        mock_qs.count.return_value = 5
        mock_project_file.objects.filter.return_value = mock_qs
        
        result = StorageService.calculate_storage_usage(org)
        
        assert result['total_gb'] == 10
        assert result['file_count'] == 5
        assert result['remaining_gb'] == 0  # 10 - 10
        assert result['usage_percentage'] == 100.0
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_over_limit(self, mock_project_file):
        """
        Detectar cuando se excede el límite
        """
        org = OrganizationFactory()  # 10 GB limit
        
        # Mock: 20 GB de uso (excede límite)
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 20 * 1024**3}
        mock_qs.count.return_value = 50
        mock_project_file.objects.filter.return_value = mock_qs
        
        result = StorageService.calculate_storage_usage(org)
        
        assert result['total_gb'] == 20
        assert result['is_over_limit'] is True
        assert result['usage_percentage'] == 100  # Capped at 100
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_handles_null_aggregate(self, mock_project_file):
        """
        BUG POTENCIAL: Manejar aggregate que retorna None
        """
        org = OrganizationFactory()
        
        # Mock: aggregate retorna None (no hay archivos)
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': None}
        mock_qs.count.return_value = 0
        mock_project_file.objects.filter.return_value = mock_qs
        
        result = StorageService.calculate_storage_usage(org)
        
        # Debe manejar None y convertir a 0
        assert result['total_bytes'] == 0
        assert result['total_gb'] == 0


# ============================================================================
# TESTS DE CACHE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestStorageServiceCache:
    """Tests de funcionalidad de cache"""
    
    def setup_method(self):
        """Limpiar cache antes de cada test"""
        cache.clear()
    
    def test_get_cache_key_format(self):
        """Verificar formato de cache key"""
        org_id = 123
        
        key = StorageService.get_cache_key(org_id)
        
        assert key == "org_storage:123"
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_caches_result(self, mock_project_file):
        """
        CRÍTICO: calculate_storage_usage debe cachear el resultado
        """
        org = OrganizationFactory()
        
        # Mock de queryset
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 0}
        mock_qs.count.return_value = 0
        mock_project_file.objects.filter.return_value = mock_qs
        
        # Primera llamada (hace 2 llamadas a filter: aggregate + count)
        result1 = StorageService.calculate_storage_usage(org)
        
        # Resetear el contador
        mock_project_file.objects.filter.reset_mock()
        
        # Segunda llamada (debe venir del cache, 0 llamadas)
        result2 = StorageService.calculate_storage_usage(org)
        
        # Verificar que NO se llamó a filter en la segunda vez (viene del cache)
        assert mock_project_file.objects.filter.call_count == 0
        
        # Resultados deben ser iguales
        assert result1 == result2
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_uses_cached_data(self, mock_project_file):
        """
        Si hay datos en cache, NO debe hacer query a la BD
        """
        org = OrganizationFactory()
        
        # Establecer datos en cache manualmente
        cache_key = StorageService.get_cache_key(org.id)
        cached_data = {
            'total_bytes': 1000,
            'total_gb': 0.001,
            'plan_limit_gb': 10,
            'usage_percentage': 0.01,
            'file_count': 1,
            'remaining_gb': 9.999,
            'is_over_limit': False
        }
        cache.set(cache_key, cached_data, 300)
        
        # Llamar al método
        result = StorageService.calculate_storage_usage(org)
        
        # NO debe haber llamado a ProjectFile (viene del cache)
        mock_project_file.objects.filter.assert_not_called()
        
        # Debe retornar los datos cacheados
        assert result == cached_data
    
    def test_invalidate_cache_removes_key(self):
        """invalidate_cache debe eliminar la clave del cache"""
        org = OrganizationFactory()
        
        # Establecer algo en cache
        cache_key = StorageService.get_cache_key(org.id)
        cache.set(cache_key, {'test': 'data'}, 300)
        
        # Verificar que está en cache
        assert cache.get(cache_key) is not None
        
        # Invalidar
        StorageService.invalidate_cache(org.id)
        
        # Verificar que se eliminó
        assert cache.get(cache_key) is None
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_cache_timeout_configuration(self, mock_project_file):
        """
        Verificar que el timeout de cache es configurable
        """
        org = OrganizationFactory()
        
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 0}
        mock_qs.count.return_value = 0
        mock_project_file.objects.filter.return_value = mock_qs
        
        # El timeout debe ser configurable via settings
        expected_timeout = getattr(settings, 'ORG_STORAGE_CACHE_TIMEOUT', 21600)
        
        with patch.object(cache, 'set', wraps=cache.set) as mock_cache_set:
            StorageService.calculate_storage_usage(org)
            
            # Verificar que se llamó a cache.set con el timeout correcto
            call_args = mock_cache_set.call_args
            assert call_args[0][2] == expected_timeout


# ============================================================================
# TESTS DE GET_STORAGE_SUMMARY
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestStorageServiceSummary:
    """Tests de get_storage_summary (para UI)"""
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_get_storage_summary_structure(self, mock_project_file):
        """Verificar estructura del dict retornado"""
        org = OrganizationFactory()
        
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 0}
        mock_qs.count.return_value = 0
        mock_project_file.objects.filter.return_value = mock_qs
        
        summary = StorageService.get_storage_summary(org)
        
        # Verificar claves esperadas
        expected_keys = {
            'used_gb', 'total_gb', 'percentage', 'remaining_gb',
            'file_count', 'status', 'is_over_limit'
        }
        assert set(summary.keys()) == expected_keys
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_get_storage_summary_status_normal(self, mock_project_file):
        """Status 'normal' cuando uso < 75%"""
        org = OrganizationFactory()
        
        # Mock: 5 GB de uso (50% de 10 GB)
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 5 * 1024**3}
        mock_qs.count.return_value = 10
        mock_project_file.objects.filter.return_value = mock_qs
        
        summary = StorageService.get_storage_summary(org)
        
        assert summary['status'] == 'normal'
        assert summary['percentage'] < 75
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_get_storage_summary_status_warning(self, mock_project_file):
        """Status 'warning' cuando uso >= 75% y < 90%"""
        org = OrganizationFactory()
        
        # Mock: 8 GB de uso (80% de 10 GB)
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 8 * 1024**3}
        mock_qs.count.return_value = 100
        mock_project_file.objects.filter.return_value = mock_qs
        
        summary = StorageService.get_storage_summary(org)
        
        assert summary['status'] == 'warning'
        assert 75 <= summary['percentage'] < 90
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_get_storage_summary_status_critical(self, mock_project_file):
        """Status 'critical' cuando uso >= 90%"""
        org = OrganizationFactory()
        
        # Mock: 9.5 GB de uso (95% de 10 GB)
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': int(9.5 * 1024**3)}
        mock_qs.count.return_value = 200
        mock_project_file.objects.filter.return_value = mock_qs
        
        summary = StorageService.get_storage_summary(org)
        
        assert summary['status'] == 'critical'
        assert summary['percentage'] >= 90


# ============================================================================
# TESTS DE CAN_UPLOAD_FILE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestStorageServiceCanUpload:
    """Tests de validación de subida de archivos"""
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_can_upload_file_within_limit(self, mock_project_file):
        """Puede subir archivo que no excede el límite"""
        # Crear org con extra storage para tener suficiente espacio
        org = OrganizationWithExtraStorageFactory(extra_storage_gb=65)  # 10 + 65 = 75 GB total
        
        # Mock: 10 GB de uso actual
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 10 * 1024**3}
        mock_qs.count.return_value = 5
        mock_project_file.objects.filter.return_value = mock_qs
        
        # Intentar subir archivo de 5 GB (10 + 5 = 15 GB, dentro del límite de 75 GB)
        file_size = 5 * 1024**3
        
        can_upload, error_msg, storage_data = StorageService.can_upload_file(org, file_size)
        
        assert can_upload is True
        assert error_msg == ""
        assert storage_data['total_gb'] == 10
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_can_upload_file_exceeds_limit(self, mock_project_file):
        """NO puede subir archivo que excede el límite"""
        org = OrganizationFactory()
        
        # Mock: 70 GB de uso actual
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 70 * 1024**3}
        mock_qs.count.return_value = 100
        mock_project_file.objects.filter.return_value = mock_qs
        
        # Intentar subir archivo de 10 GB (excedería el límite de 75 GB)
        file_size = 10 * 1024**3
        
        can_upload, error_msg, storage_data = StorageService.can_upload_file(org, file_size)
        
        assert can_upload is False
        assert "No se puede subir el archivo" in error_msg
        assert "MB" in error_msg  # Debe mostrar tamaños en MB
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_can_upload_file_exactly_at_limit(self, mock_project_file):
        """Archivo que llega exactamente al límite se permite"""
        # Crear org con extra storage para tener 75 GB total
        org = OrganizationWithExtraStorageFactory(extra_storage_gb=65)  # 10 + 65 = 75 GB total
        
        # Mock: 70 GB de uso actual
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 70 * 1024**3}
        mock_qs.count.return_value = 100
        mock_project_file.objects.filter.return_value = mock_qs
        
        # Archivo de 5 GB (70 + 5 = 75, exactamente el límite)
        file_size = 5 * 1024**3
        
        can_upload, error_msg, storage_data = StorageService.can_upload_file(org, file_size)
        
        assert can_upload is True
        assert error_msg == ""


# ============================================================================
# TESTS DE FORMAT_SIZE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestStorageServiceFormatSize:
    """Tests de formateo de tamaño de archivos"""
    
    def test_format_size_zero_bytes(self):
        """0 bytes debe mostrar '0 B'"""
        formatted = StorageService.format_size(0)
        assert formatted == "0 B"
    
    def test_format_size_bytes(self):
        """Bytes deben mostrarse correctamente"""
        formatted = StorageService.format_size(500)
        assert formatted == "500 B"
    
    def test_format_size_kilobytes(self):
        """Kilobytes deben mostrarse correctamente"""
        formatted = StorageService.format_size(1024)
        assert formatted == "1.0 KB"
    
    def test_format_size_megabytes(self):
        """Megabytes deben mostrarse correctamente"""
        formatted = StorageService.format_size(1024**2)
        assert formatted == "1.0 MB"
    
    def test_format_size_gigabytes(self):
        """Gigabytes deben mostrarse correctamente"""
        formatted = StorageService.format_size(1024**3)
        assert formatted == "1.0 GB"
    
    def test_format_size_terabytes(self):
        """Terabytes deben mostrarse correctamente"""
        formatted = StorageService.format_size(1024**4)
        assert formatted == "1.0 TB"
    
    def test_format_size_decimal_values(self):
        """Valores decimales deben redondearse a 2 decimales"""
        formatted = StorageService.format_size(1536)  # 1.5 KB
        assert formatted == "1.5 KB"


# ============================================================================
# TESTS DE MANEJO DE ERRORES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestStorageServiceErrorHandling:
    """Tests de manejo de errores y edge cases"""
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_handles_exception(self, mock_project_file):
        """
        BUG POTENCIAL: Manejar excepciones durante el cálculo
        """
        org = OrganizationFactory()
        
        # Mock que lanza excepción
        mock_project_file.objects.filter.side_effect = Exception("Database error")
        
        result = StorageService.calculate_storage_usage(org)
        
        # Debe retornar datos de fallback, no crashear
        assert result['error'] is True
        assert result['total_gb'] == 0
        assert result['plan_limit_gb'] == 75
    
    @patch('apps.orgs.storage_service.ProjectFile')
    def test_calculate_storage_with_zero_limit(self, mock_project_file):
        """
        EDGE CASE: ¿Qué pasa si plan_limit_gb es 0?
        """
        org = OrganizationFactory(extra_storage_gb=-75)  # Reducir a 0
        
        mock_qs = Mock()
        mock_qs.aggregate.return_value = {'total': 0}
        mock_qs.count.return_value = 0
        mock_project_file.objects.filter.return_value = mock_qs
        
        result = StorageService.calculate_storage_usage(org)
        
        # Con límite 0, usage_percentage debe ser 100 (para evitar división por 0)
        assert result['usage_percentage'] == 100
        assert result['plan_limit_gb'] == 0
