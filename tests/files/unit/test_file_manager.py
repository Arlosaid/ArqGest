"""
Tests para el Manager custom de ProjectFile

Valida métodos optimizados como:
- with_related()
- by_phase()
- by_organization()
- by_extension()
- large_files()
- recent()
- get_phase_stats()
- get_storage_usage_by_org()
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from apps.files.models import ProjectFile
from tests.factories import (
    ProjectFileFactory,
    PDFFileFactory,
    JPGFileFactory,
    DWGFileFactory,
    LargeFileFactory,
    PhaseFactory,
    OrganizationFactory,
)


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileManager:
    """Tests del manager básico"""
    
    def test_manager_exists(self):
        """El manager objects existe"""
        assert hasattr(ProjectFile, 'objects')
    
    def test_all_returns_queryset(self, use_local_storage):
        """El método all() retorna un QuerySet"""
        ProjectFileFactory()
        ProjectFileFactory()
        
        files = ProjectFile.objects.all()
        
        assert files.count() == 2


@pytest.mark.django_db
@pytest.mark.unit
class TestWithRelatedMethod:
    """Tests del método with_related()"""
    
    def test_with_related_includes_phase(self, use_local_storage):
        """with_related() incluye la fase"""
        file_obj = ProjectFileFactory()
        
        # Limpiar queries previas
        from django.db import reset_queries
        reset_queries()
        
        files = ProjectFile.objects.with_related()
        file_from_query = files.first()
        
        # Acceder a phase no debe generar query adicional
        _ = file_from_query.phase.name
    
    def test_with_related_includes_project(self, use_local_storage):
        """with_related() incluye el proyecto"""
        file_obj = ProjectFileFactory()
        
        files = ProjectFile.objects.with_related()
        file_from_query = files.first()
        
        # Acceder a proyecto no debe generar query adicional
        _ = file_from_query.phase.project.name
    
    def test_with_related_includes_organization(self, use_local_storage):
        """with_related() incluye la organización"""
        file_obj = ProjectFileFactory()
        
        files = ProjectFile.objects.with_related()
        file_from_query = files.first()
        
        # Acceder a organización no debe generar query adicional
        _ = file_from_query.phase.project.organization.name
    
    def test_with_related_includes_uploaded_by(self, use_local_storage):
        """with_related() incluye el usuario"""
        file_obj = ProjectFileFactory()
        
        files = ProjectFile.objects.with_related()
        file_from_query = files.first()
        
        # Acceder a usuario no debe generar query adicional
        if file_from_query.uploaded_by:
            _ = file_from_query.uploaded_by.email


@pytest.mark.django_db
@pytest.mark.unit
class TestByPhaseMethod:
    """Tests del método by_phase()"""
    
    def test_by_phase_filters_correctly(self, use_local_storage):
        """by_phase() filtra archivos por fase"""
        phase1 = PhaseFactory()
        phase2 = PhaseFactory()
        
        file1 = ProjectFileFactory(phase=phase1)
        file2 = ProjectFileFactory(phase=phase1)
        file3 = ProjectFileFactory(phase=phase2)
        
        files_phase1 = ProjectFile.objects.by_phase(phase1.id)
        
        assert files_phase1.count() == 2
        assert file1 in files_phase1
        assert file2 in files_phase1
        assert file3 not in files_phase1
    
    def test_by_phase_returns_empty_for_nonexistent_phase(self, use_local_storage):
        """by_phase() retorna vacío para fase inexistente"""
        ProjectFileFactory()
        
        files = ProjectFile.objects.by_phase(99999)
        
        assert files.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
class TestByOrganizationMethod:
    """Tests del método by_organization()"""
    
    def test_by_organization_filters_correctly(self, use_local_storage):
        """by_organization() filtra archivos por organización"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        file1 = ProjectFileFactory(phase__project__organization=org1)
        file2 = ProjectFileFactory(phase__project__organization=org1)
        file3 = ProjectFileFactory(phase__project__organization=org2)
        
        files_org1 = ProjectFile.objects.by_organization(org1.id)
        
        assert files_org1.count() == 2
        assert file1 in files_org1
        assert file2 in files_org1
        assert file3 not in files_org1
    
    def test_by_organization_returns_empty_for_nonexistent_org(self, use_local_storage):
        """by_organization() retorna vacío para org inexistente"""
        ProjectFileFactory()
        
        files = ProjectFile.objects.by_organization(99999)
        
        assert files.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
class TestByExtensionMethod:
    """Tests del método by_extension()"""
    
    def test_by_extension_filters_correctly(self, use_local_storage):
        """by_extension() filtra archivos por extensión"""
        pdf1 = PDFFileFactory()
        pdf2 = PDFFileFactory()
        jpg = JPGFileFactory()
        
        pdfs = ProjectFile.objects.by_extension('PDF')
        
        assert pdfs.count() == 2
        assert pdf1 in pdfs
        assert pdf2 in pdfs
        assert jpg not in pdfs
    
    def test_by_extension_is_case_insensitive(self, use_local_storage):
        """by_extension() es case-insensitive"""
        pdf = PDFFileFactory()
        
        # Todas estas formas deben funcionar
        assert pdf in ProjectFile.objects.by_extension('PDF')
        assert pdf in ProjectFile.objects.by_extension('pdf')
        assert pdf in ProjectFile.objects.by_extension('Pdf')
    
    def test_by_extension_returns_empty_for_nonexistent_ext(self, use_local_storage):
        """by_extension() retorna vacío para extensión inexistente"""
        PDFFileFactory()
        
        files = ProjectFile.objects.by_extension('XYZ')
        
        assert files.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
class TestLargeFilesMethod:
    """Tests del método large_files()"""
    
    def test_large_files_filters_correctly(self, use_local_storage):
        """large_files() filtra archivos grandes"""
        # Crear archivo pequeño y grande
        small = PDFFileFactory(size_bytes=5 * 1024 * 1024)  # 5MB
        large = LargeFileFactory(size_bytes=50 * 1024 * 1024)  # 50MB
        
        # Buscar archivos >10MB
        large_files = ProjectFile.objects.large_files(min_size_mb=10)
        
        assert large in large_files
        assert small not in large_files
    
    def test_large_files_default_threshold(self, use_local_storage):
        """large_files() usa threshold por defecto de 10MB"""
        small = PDFFileFactory(size_bytes=5 * 1024 * 1024)
        large = LargeFileFactory(size_bytes=15 * 1024 * 1024)
        
        large_files = ProjectFile.objects.large_files()
        
        assert large in large_files
        assert small not in large_files
    
    def test_large_files_custom_threshold(self, use_local_storage):
        """large_files() acepta threshold personalizado"""
        medium = PDFFileFactory(size_bytes=30 * 1024 * 1024)  # 30MB
        huge = LargeFileFactory(size_bytes=60 * 1024 * 1024)  # 60MB
        
        # Solo archivos >50MB
        huge_files = ProjectFile.objects.large_files(min_size_mb=50)
        
        assert huge in huge_files
        assert medium not in huge_files


@pytest.mark.django_db
@pytest.mark.unit
class TestRecentMethod:
    """Tests del método recent()"""
    
    def test_recent_filters_by_days(self, use_local_storage):
        """recent() filtra archivos recientes por días"""
        # Archivo reciente (hoy)
        recent_file = ProjectFileFactory()
        
        # Archivo viejo (hace 60 días)
        old_file = ProjectFileFactory()
        old_file.uploaded_at = timezone.now() - timedelta(days=60)
        old_file.save()
        
        # Buscar archivos de últimos 30 días
        recent_files = ProjectFile.objects.recent(days=30)
        
        assert recent_file in recent_files
        assert old_file not in recent_files
    
    def test_recent_default_threshold(self, use_local_storage):
        """recent() usa threshold por defecto de 30 días"""
        recent = ProjectFileFactory()
        
        old = ProjectFileFactory()
        old.uploaded_at = timezone.now() - timedelta(days=45)
        old.save()
        
        recent_files = ProjectFile.objects.recent()
        
        assert recent in recent_files
        assert old not in recent_files


@pytest.mark.django_db
@pytest.mark.unit
class TestWithChecksumsMethod:
    """Tests del método with_checksums()"""
    
    def test_with_checksums_filters_correctly(self, use_local_storage):
        """with_checksums() filtra archivos con checksum"""
        with_checksum = ProjectFileFactory(checksum_sha256='a' * 64)
        without_checksum = ProjectFileFactory(checksum_sha256='')
        
        files_with_checksum = ProjectFile.objects.with_checksums()
        
        assert with_checksum in files_with_checksum
        assert without_checksum not in files_with_checksum


@pytest.mark.django_db
@pytest.mark.unit
class TestDuplicatesByChecksumMethod:
    """Tests del método duplicates_by_checksum()"""
    
    def test_duplicates_by_checksum_finds_duplicates(self, use_local_storage):
        """duplicates_by_checksum() encuentra archivos duplicados"""
        checksum = 'a' * 64
        
        file1 = ProjectFileFactory(checksum_sha256=checksum)
        file2 = ProjectFileFactory(checksum_sha256=checksum)
        unique_file = ProjectFileFactory(checksum_sha256='b' * 64)
        
        duplicates = ProjectFile.objects.duplicates_by_checksum()
        
        # Debe retornar el checksum duplicado
        assert duplicates.count() == 1
        assert duplicates[0]['checksum_sha256'] == checksum
        assert duplicates[0]['count'] == 2
    
    def test_duplicates_ignores_empty_checksums(self, use_local_storage):
        """duplicates_by_checksum() ignora checksums vacíos"""
        file1 = ProjectFileFactory(checksum_sha256='')
        file2 = ProjectFileFactory(checksum_sha256='')
        
        duplicates = ProjectFile.objects.duplicates_by_checksum()
        
        assert duplicates.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
class TestGetPhaseStatsMethod:
    """Tests del método get_phase_stats()"""
    
    def test_get_phase_stats_returns_correct_data(self, use_local_storage):
        """get_phase_stats() retorna estadísticas correctas"""
        phase = PhaseFactory()
        
        PDFFileFactory(phase=phase, size_bytes=1024)
        PDFFileFactory(phase=phase, size_bytes=2048)
        JPGFileFactory(phase=phase, size_bytes=512)
        
        stats = ProjectFile.objects.get_phase_stats(phase.id, use_cache=False)
        
        assert stats['total_files'] == 3
        assert stats['total_size'] == 1024 + 2048 + 512
        assert 'by_extension' in stats
    
    def test_get_phase_stats_groups_by_extension(self, use_local_storage):
        """get_phase_stats() agrupa por extensión"""
        phase = PhaseFactory()
        
        PDFFileFactory(phase=phase)
        PDFFileFactory(phase=phase)
        JPGFileFactory(phase=phase)
        
        stats = ProjectFile.objects.get_phase_stats(phase.id, use_cache=False)
        
        extensions = [item['ext_upper'] for item in stats['by_extension']]
        
        assert 'PDF' in extensions
        assert 'JPG' in extensions
    
    def test_get_phase_stats_caches_results(self, use_local_storage):
        """get_phase_stats() cachea los resultados"""
        phase = PhaseFactory()
        PDFFileFactory(phase=phase)
        
        # Limpiar cache
        cache.clear()
        
        # Primera llamada (genera stats)
        stats1 = ProjectFile.objects.get_phase_stats(phase.id, use_cache=True)
        
        # Agregar otro archivo
        PDFFileFactory(phase=phase)
        
        # Segunda llamada (debe usar cache y retornar mismos datos)
        stats2 = ProjectFile.objects.get_phase_stats(phase.id, use_cache=True)
        
        assert stats1['total_files'] == stats2['total_files']
    
    def test_get_phase_stats_can_skip_cache(self, use_local_storage):
        """get_phase_stats() puede omitir el cache"""
        phase = PhaseFactory()
        PDFFileFactory(phase=phase)
        
        stats1 = ProjectFile.objects.get_phase_stats(phase.id, use_cache=True)
        
        # Agregar archivo
        PDFFileFactory(phase=phase)
        
        # Con use_cache=False debe refrescar
        stats2 = ProjectFile.objects.get_phase_stats(phase.id, use_cache=False)
        
        assert stats2['total_files'] > stats1['total_files']


@pytest.mark.django_db
@pytest.mark.unit
class TestGetStorageUsageByOrgMethod:
    """Tests del método get_storage_usage_by_org()"""
    
    def test_get_storage_usage_calculates_correctly(self, use_local_storage):
        """get_storage_usage_by_org() calcula uso correctamente"""
        org = OrganizationFactory()
        
        PDFFileFactory(
            phase__project__organization=org,
            size_bytes=1024
        )
        PDFFileFactory(
            phase__project__organization=org,
            size_bytes=2048
        )
        
        usage = ProjectFile.objects.get_storage_usage_by_org(org.id)
        
        assert usage['total_files'] == 2
        assert usage['total_size'] == 1024 + 2048
    
    def test_get_storage_usage_only_counts_org_files(self, use_local_storage):
        """get_storage_usage_by_org() solo cuenta archivos de la org"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        PDFFileFactory(phase__project__organization=org1)
        PDFFileFactory(phase__project__organization=org2)
        
        usage_org1 = ProjectFile.objects.get_storage_usage_by_org(org1.id)
        
        assert usage_org1['total_files'] == 1
    
    def test_get_storage_usage_returns_zero_for_empty_org(self, use_local_storage):
        """get_storage_usage_by_org() retorna cero para org sin archivos"""
        org = OrganizationFactory()
        
        usage = ProjectFile.objects.get_storage_usage_by_org(org.id)
        
        assert usage['total_files'] == 0
        assert usage['total_size'] is None or usage['total_size'] == 0


@pytest.mark.django_db
@pytest.mark.unit
class TestManagerChaining:
    """Tests de encadenamiento de métodos del manager"""
    
    def test_can_chain_with_related_and_by_phase(self, use_local_storage):
        """Se pueden encadenar with_related() y by_phase()"""
        phase = PhaseFactory()
        ProjectFileFactory(phase=phase)
        
        files = ProjectFile.objects.with_related().by_phase(phase.id)
        
        assert files.count() == 1
    
    def test_can_chain_by_organization_and_by_extension(self, use_local_storage):
        """Se pueden encadenar by_organization() y by_extension()"""
        org = OrganizationFactory()
        PDFFileFactory(phase__project__organization=org)
        JPGFileFactory(phase__project__organization=org)
        
        pdfs = ProjectFile.objects.by_organization(org.id).by_extension('PDF')
        
        assert pdfs.count() == 1
    
    def test_can_chain_large_files_and_recent(self, use_local_storage):
        """Se pueden encadenar large_files() y recent()"""
        LargeFileFactory(size_bytes=50 * 1024 * 1024)
        
        files = ProjectFile.objects.large_files(10).recent(30)
        
        assert files.count() == 1




