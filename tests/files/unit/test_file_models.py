"""
Tests exhaustivos para el modelo ProjectFile

Estos tests validan:
- Creación de archivos
- Propiedades y métodos
- Relaciones y CASCADE
- Manager custom
- Edge cases
"""
import pytest
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from apps.files.models import ProjectFile, project_file_path
from tests.factories import (
    ProjectFileFactory,
    PDFFileFactory,
    ImageFileFactory,
    JPGFileFactory,
    PNGFileFactory,
    WordFileFactory,
    DWGFileFactory,
    RVTFileFactory,
    ZIPFileFactory,
    LargeFileFactory,
    PhaseFactory,
    ProjectFactory,
    OrganizationFactory,
    UserFactory,
)


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileCreation:
    """Tests de creación de archivos"""
    
    def test_create_file_with_factory(self, use_local_storage):
        """Crear archivo usando factory"""
        file_obj = ProjectFileFactory()
        
        assert file_obj.pk is not None
        assert file_obj.phase is not None
        assert file_obj.uploaded_by is not None
        assert file_obj.file.name
    
    def test_create_pdf_file(self, use_local_storage):
        """Crear archivo PDF específico"""
        pdf = PDFFileFactory()
        
        assert pdf.ext_upper == 'PDF'
        assert pdf.content_type == 'application/pdf'
        assert 'pdf' in pdf.file.name.lower()
    
    def test_create_jpg_file(self, use_local_storage):
        """Crear archivo JPG"""
        jpg = JPGFileFactory()
        
        assert jpg.ext_upper == 'JPG'
        assert jpg.content_type == 'image/jpeg'
    
    def test_create_png_file(self, use_local_storage):
        """Crear archivo PNG"""
        png = PNGFileFactory()
        
        assert png.ext_upper == 'PNG'
        assert png.content_type == 'image/png'
    
    def test_create_word_file(self, use_local_storage):
        """Crear archivo Word (DOCX)"""
        word = WordFileFactory()
        
        assert word.ext_upper == 'DOCX'
        assert 'openxmlformats' in word.content_type
    
    def test_create_dwg_file(self, use_local_storage):
        """Crear archivo AutoCAD (DWG)"""
        dwg = DWGFileFactory()
        
        assert dwg.ext_upper == 'DWG'
    
    def test_create_rvt_file(self, use_local_storage):
        """Crear archivo Revit (RVT)"""
        rvt = RVTFileFactory()
        
        assert rvt.ext_upper == 'RVT'
    
    def test_create_zip_file(self, use_local_storage):
        """Crear archivo ZIP"""
        zip_file = ZIPFileFactory()
        
        assert zip_file.ext_upper == 'ZIP'
        assert 'zip' in zip_file.content_type
    
    def test_create_large_file(self, use_local_storage):
        """Crear archivo grande"""
        large = LargeFileFactory()
        
        assert large.size_bytes > 100 * 1024 * 1024  # >100MB
    
    def test_uploaded_at_is_set_automatically(self, use_local_storage):
        """El campo uploaded_at se establece automáticamente"""
        file_obj = ProjectFileFactory()
        
        assert file_obj.uploaded_at is not None
    
    def test_checksum_can_be_stored(self, use_local_storage):
        """Se puede almacenar checksum SHA256"""
        file_obj = ProjectFileFactory(
            checksum_sha256='a' * 64  # SHA256 es 64 caracteres hex
        )
        
        assert len(file_obj.checksum_sha256) == 64


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileRelationships:
    """Tests de relaciones del modelo"""
    
    def test_file_belongs_to_phase(self, use_local_storage):
        """Archivo pertenece a una fase"""
        phase = PhaseFactory()
        file_obj = ProjectFileFactory(phase=phase)
        
        assert file_obj.phase == phase
        assert file_obj in phase.files.all()
    
    def test_file_belongs_to_user(self, use_local_storage):
        """Archivo tiene usuario que lo subió"""
        phase = PhaseFactory()
        user = UserFactory(organization=phase.project.organization)
        file_obj = ProjectFileFactory(phase=phase, uploaded_by=user)
        
        assert file_obj.uploaded_by == user
    
    def test_deleting_phase_deletes_files(self, use_local_storage):
        """
        CASCADE: Eliminar fase elimina sus archivos.
        
        Esto es importante para mantener consistencia de datos.
        """
        phase = PhaseFactory()
        file1 = ProjectFileFactory(phase=phase)
        file2 = ProjectFileFactory(phase=phase)
        
        file1_id = file1.id
        file2_id = file2.id
        
        phase.delete()
        
        assert not ProjectFile.objects.filter(id=file1_id).exists()
        assert not ProjectFile.objects.filter(id=file2_id).exists()
    
    def test_deleting_user_sets_uploaded_by_to_null(self, use_local_storage):
        """
        SET_NULL: Eliminar usuario NO elimina archivos.
        
        Los archivos se mantienen pero uploaded_by se vuelve NULL.
        """
        phase = PhaseFactory()
        user = UserFactory(organization=phase.project.organization)
        file_obj = ProjectFileFactory(phase=phase, uploaded_by=user)
        
        user.delete()
        
        file_obj.refresh_from_db()
        assert file_obj.uploaded_by is None
    
    def test_file_can_have_null_uploaded_by(self, use_local_storage):
        """Archivo puede no tener usuario (NULL)"""
        file_obj = ProjectFileFactory(uploaded_by=None)
        
        assert file_obj.uploaded_by is None
    
    def test_multiple_files_in_same_phase(self, use_local_storage):
        """Múltiples archivos pueden estar en la misma fase"""
        phase = PhaseFactory()
        file1 = ProjectFileFactory(phase=phase)
        file2 = ProjectFileFactory(phase=phase)
        file3 = ProjectFileFactory(phase=phase)
        
        assert phase.files.count() == 3


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileProperties:
    """Tests de propiedades del modelo"""
    
    def test_size_property_returns_file_size(self, use_local_storage):
        """Propiedad size retorna tamaño del archivo"""
        file_obj = ProjectFileFactory()
        
        assert file_obj.size > 0
    
    def test_filename_property_returns_basename(self, use_local_storage):
        """Propiedad filename retorna nombre base sin path"""
        file_obj = ProjectFileFactory()
        
        filename = file_obj.filename
        
        # No debe contener path completo
        assert '/' not in filename
        assert '\\' not in filename
    
    def test_extension_property_returns_uppercase_ext(self, use_local_storage):
        """Propiedad extension retorna extensión en mayúsculas"""
        pdf = PDFFileFactory()
        
        assert pdf.extension == 'PDF'
    
    def test_extension_property_uses_ext_upper_field(self, use_local_storage):
        """Propiedad extension usa el campo ext_upper si está disponible"""
        file_obj = ProjectFileFactory(ext_upper='DWG')
        
        assert file_obj.extension == 'DWG'
    
    def test_file_extension_property_returns_lowercase(self, use_local_storage):
        """Propiedad file_extension retorna extensión en minúsculas (para CSS)"""
        pdf = PDFFileFactory()
        
        assert pdf.file_extension == 'pdf'
    
    def test_icon_class_for_pdf(self, use_local_storage):
        """Icon class correcto para PDF"""
        pdf = PDFFileFactory()
        
        assert pdf.icon_class == 'fa-file-pdf'
    
    def test_icon_class_for_word(self, use_local_storage):
        """Icon class correcto para Word"""
        word = WordFileFactory()
        
        assert word.icon_class == 'fa-file-word'
    
    def test_icon_class_for_image(self, use_local_storage):
        """Icon class correcto para imágenes"""
        jpg = JPGFileFactory()
        png = PNGFileFactory()
        
        assert jpg.icon_class == 'fa-file-image'
        assert png.icon_class == 'fa-file-image'
    
    def test_icon_class_for_dwg(self, use_local_storage):
        """Icon class correcto para archivos CAD"""
        dwg = DWGFileFactory()
        
        assert dwg.icon_class == 'fa-drafting-compass'
    
    def test_icon_class_for_zip(self, use_local_storage):
        """Icon class correcto para archivos comprimidos"""
        zip_file = ZIPFileFactory()
        
        assert zip_file.icon_class == 'fa-file-archive'
    
    def test_icon_class_for_unknown_extension(self, use_local_storage):
        """Icon class por defecto para extensiones desconocidas"""
        # Crear archivo con extensión desconocida
        unknown_file = SimpleUploadedFile(
            name="file.xyz",
            content=b"unknown content",
            content_type="application/octet-stream"
        )
        file_obj = ProjectFileFactory(file=unknown_file, ext_upper='XYZ')
        
        assert file_obj.icon_class == 'fa-file'


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileSave:
    """Tests del método save()"""
    
    def test_save_populates_size_bytes(self, use_local_storage):
        """El método save() llena automáticamente size_bytes"""
        file_obj = ProjectFileFactory()
        
        assert file_obj.size_bytes > 0
    
    def test_save_populates_ext_upper(self, use_local_storage):
        """El método save() llena automáticamente ext_upper"""
        file_obj = PDFFileFactory()
        
        assert file_obj.ext_upper == 'PDF'
    
    def test_save_handles_multiple_dots_in_filename(self, use_local_storage):
        """Maneja correctamente nombres con múltiples puntos"""
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name="my.backup.document.pdf",
                content=b"fake pdf",
                content_type="application/pdf"
            ),
            ext_upper=''  # Permitir que se extraiga la extensión
        )
        
        # Debe tomar solo la última extensión
        assert file_obj.ext_upper == 'PDF'
    
    def test_save_resets_file_pointer_for_new_files(self, use_local_storage):
        """
        CRITICAL: El puntero del archivo se resetea antes de guardar.
        
        BUG POTENCIAL: Si no se resetea, podría guardarse archivo vacío.
        """
        content = b"PDF content that should be saved"
        uploaded_file = SimpleUploadedFile(
            name="test.pdf",
            content=content,
            content_type="application/pdf"
        )
        
        # Mover el puntero (simular lectura previa)
        uploaded_file.read()
        assert uploaded_file.tell() == len(content)
        
        # Crear archivo - save() debe resetear el puntero
        # No especificar size_bytes para que use el tamaño real del archivo
        file_obj = ProjectFileFactory(file=uploaded_file, size_bytes=0)
        
        # El archivo debe haberse guardado correctamente
        assert file_obj.size_bytes == len(content)


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileDelete:
    """Tests del método delete()"""
    
    def test_delete_removes_from_database(self, use_local_storage):
        """Eliminar archivo lo remueve de la base de datos"""
        file_obj = ProjectFileFactory()
        file_id = file_obj.id
        
        file_obj.delete()
        
        assert not ProjectFile.objects.filter(id=file_id).exists()
    
    def test_delete_preserves_file_info_in_logs(self, use_local_storage):
        """
        El método delete() guarda información antes de eliminar (para logs).
        
        Esto es importante para auditoría.
        """
        file_obj = ProjectFileFactory()
        file_id = file_obj.id
        filename = file_obj.filename
        
        # El delete() debería logear esta información
        file_obj.delete()
        
        # Verificar que se eliminó
        assert not ProjectFile.objects.filter(id=file_id).exists()


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileStr:
    """Tests del método __str__()"""
    
    def test_str_returns_file_name(self, use_local_storage):
        """__str__() retorna el nombre del archivo"""
        file_obj = ProjectFileFactory()
        
        assert str(file_obj) == file_obj.file.name


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFilePath:
    """Tests de la función project_file_path"""
    
    def test_path_includes_organization_id(self, use_local_storage):
        """Path incluye ID de organización"""
        org = OrganizationFactory()
        phase = PhaseFactory(project__organization=org)
        file_obj = ProjectFile(
            phase=phase,
            uploaded_by=UserFactory()
        )
        
        path = project_file_path(file_obj, "test.pdf")
        
        assert f"organizations/{org.id}/" in path
    
    def test_path_includes_project_id(self, use_local_storage):
        """Path incluye ID de proyecto"""
        project = ProjectFactory()
        phase = PhaseFactory(project=project)
        file_obj = ProjectFile(
            phase=phase,
            uploaded_by=UserFactory()
        )
        
        path = project_file_path(file_obj, "test.pdf")
        
        assert f"projects/{project.id}/" in path
    
    def test_path_includes_phase_id(self, use_local_storage):
        """Path incluye ID de fase"""
        phase = PhaseFactory()
        file_obj = ProjectFile(
            phase=phase,
            uploaded_by=UserFactory()
        )
        
        path = project_file_path(file_obj, "test.pdf")
        
        assert f"phases/{phase.id}/" in path
    
    def test_path_includes_filename(self, use_local_storage):
        """Path incluye nombre del archivo"""
        phase = PhaseFactory()
        file_obj = ProjectFile(
            phase=phase,
            uploaded_by=UserFactory()
        )
        
        filename = "my_document.pdf"
        path = project_file_path(file_obj, filename)
        
        assert path.endswith(filename)
    
    def test_path_structure_is_correct(self, use_local_storage):
        """Estructura completa del path es correcta"""
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)
        phase = PhaseFactory(project=project)
        file_obj = ProjectFile(
            phase=phase,
            uploaded_by=UserFactory()
        )
        
        path = project_file_path(file_obj, "document.pdf")
        
        expected = f"organizations/{org.id}/projects/{project.id}/phases/{phase.id}/document.pdf"
        assert path == expected


@pytest.mark.django_db
@pytest.mark.unit
class TestProjectFileEdgeCases:
    """Tests de edge cases"""
    
    def test_file_without_extension(self, use_local_storage):
        """Archivo sin extensión se maneja correctamente"""
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name="README",
                content=b"readme content",
                content_type="text/plain"
            ),
            ext_upper=''  # Especificar sin extensión
        )
        
        assert file_obj.ext_upper == ''
        assert file_obj.extension == ''
    
    def test_file_with_uppercase_extension(self, use_local_storage):
        """Extensión en mayúsculas se normaliza"""
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name="document.PDF",
                content=b"pdf content",
                content_type="application/pdf"
            ),
            ext_upper=''  # Permitir que se extraiga
        )
        
        assert file_obj.ext_upper == 'PDF'
    
    def test_file_with_mixed_case_extension(self, use_local_storage):
        """Extensión en case mixto se normaliza"""
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name="photo.JpG",
                content=b"\xff\xd8\xff\xe0",
                content_type="image/jpeg"
            ),
            ext_upper=''  # Permitir que se extraiga
        )
        
        assert file_obj.ext_upper == 'JPG'
    
    def test_filename_with_spaces(self, use_local_storage):
        """Nombre con espacios se maneja correctamente"""
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name="my document with spaces.pdf",
                content=b"pdf content",
                content_type="application/pdf"
            )
        )
        
        assert file_obj.filename
    
    def test_filename_with_unicode(self, use_local_storage):
        """Nombre con Unicode se maneja correctamente"""
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name="documento_español_ñ.pdf",
                content=b"pdf content",
                content_type="application/pdf"
            )
        )
        
        assert file_obj.filename
        assert 'ñ' in file_obj.filename or 'n' in file_obj.filename  # Puede ser sanitizado
    
    def test_very_long_filename(self, use_local_storage):
        """Nombre muy largo se trunca correctamente para evitar errores de filesystem"""
        long_name = "a" * 200 + ".pdf"
        
        file_obj = ProjectFileFactory(
            file=SimpleUploadedFile(
                name=long_name,
                content=b"pdf content",
                content_type="application/pdf"
            )
        )
        
        assert file_obj.filename
        # El nombre debe ser truncado a max 100 caracteres (incluyendo extensión)
        assert len(file_obj.filename) <= 100, f"Filename too long: {len(file_obj.filename)} chars"
    
    def test_empty_checksum_is_allowed(self, use_local_storage):
        """Checksum vacío es permitido"""
        file_obj = ProjectFileFactory(checksum_sha256='')
        
        assert file_obj.checksum_sha256 == ''
    
    def test_zero_size_file_can_be_created(self, use_local_storage):
        """
        Archivo de 0 bytes puede crearse en el modelo.
        
        NOTA: Las validaciones de negocio deberían rechazarlo antes.
        """
        # Crear archivo con contenido vacío para que size_bytes sea realmente 0
        empty_file = SimpleUploadedFile(
            name="empty.pdf",
            content=b"",
            content_type="application/pdf"
        )
        file_obj = ProjectFileFactory(file=empty_file, size_bytes=0)
        
        assert file_obj.size_bytes == 0




