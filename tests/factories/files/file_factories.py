"""
Factories para modelos de Files

Proporciona factories para crear archivos de prueba con diferentes
características: documentos, imágenes, CAD, archivos maliciosos, etc.
"""
import factory
from factory.django import DjangoModelFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.files.models import ProjectFile


class ProjectFileFactory(DjangoModelFactory):
    """Factory base para crear archivos de proyecto"""
    
    class Meta:
        model = ProjectFile
    
    phase = factory.SubFactory('tests.factories.projects.project_factories.PhaseFactory')
    uploaded_by = factory.SubFactory('tests.factories.accounts.account_factories.UserFactory')
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"test_file_{factory.Faker('uuid4')}.pdf",
            content=b"PDF test content",
            content_type="application/pdf"
        )
    )
    
    size_bytes = 1024
    ext_upper = 'PDF'
    content_type = 'application/pdf'
    checksum_sha256 = factory.Faker('sha256')
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        SECURITY FIX: Asegurar que uploaded_by pertenece a la misma organización
        que el proyecto antes de crear la instancia.
        """
        # Si se proporciona phase y uploaded_by, asegurar que estén en la misma org
        if 'phase' in kwargs and 'uploaded_by' in kwargs and kwargs['uploaded_by'] is not None:
            phase = kwargs['phase']
            uploaded_by = kwargs['uploaded_by']
            project_org = phase.project.organization
            
            if uploaded_by.organization != project_org:
                uploaded_by.organization = project_org
                uploaded_by.save()
        
        return super()._create(model_class, *args, **kwargs)


class PDFFileFactory(ProjectFileFactory):
    """Factory para archivos PDF"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"document_{factory.Faker('uuid4')}.pdf",
            content=b"%PDF-1.4 fake pdf content",
            content_type="application/pdf"
        )
    )
    ext_upper = 'PDF'
    content_type = 'application/pdf'
    size_bytes = 2048


class ImageFileFactory(ProjectFileFactory):
    """Factory base para archivos de imagen"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"image_{factory.Faker('uuid4')}.jpg",
            content=b"\xff\xd8\xff\xe0\x00\x10JFIF fake jpeg",
            content_type="image/jpeg"
        )
    )
    ext_upper = 'JPG'
    content_type = 'image/jpeg'
    size_bytes = 512000


class JPGFileFactory(ImageFileFactory):
    """Factory para archivos JPG"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"photo_{factory.Faker('uuid4')}.jpg",
            content=b"\xff\xd8\xff\xe0\x00\x10JFIF fake jpeg",
            content_type="image/jpeg"
        )
    )
    ext_upper = 'JPG'
    content_type = 'image/jpeg'


class PNGFileFactory(ImageFileFactory):
    """Factory para archivos PNG"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"image_{factory.Faker('uuid4')}.png",
            content=b"\x89PNG\r\n\x1a\n fake png",
            content_type="image/png"
        )
    )
    ext_upper = 'PNG'
    content_type = 'image/png'


class WordFileFactory(ProjectFileFactory):
    """Factory para archivos Word (DOCX)"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"document_{factory.Faker('uuid4')}.docx",
            content=b"PK fake docx content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    )
    ext_upper = 'DOCX'
    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    size_bytes = 15360


class ExcelFileFactory(ProjectFileFactory):
    """Factory para archivos Excel (XLSX)"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"spreadsheet_{factory.Faker('uuid4')}.xlsx",
            content=b"PK fake xlsx content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    )
    ext_upper = 'XLSX'
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    size_bytes = 20480


class DWGFileFactory(ProjectFileFactory):
    """Factory para archivos AutoCAD (DWG)"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"drawing_{factory.Faker('uuid4')}.dwg",
            content=b"AC1021 fake dwg content",
            content_type="application/acad"
        )
    )
    ext_upper = 'DWG'
    content_type = 'application/acad'
    size_bytes = 2048000


class RVTFileFactory(ProjectFileFactory):
    """Factory para archivos Revit (RVT)"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"model_{factory.Faker('uuid4')}.rvt",
            content=b"fake revit content",
            content_type="application/octet-stream"
        )
    )
    ext_upper = 'RVT'
    content_type = 'application/octet-stream'
    size_bytes = 10485760


class ZIPFileFactory(ProjectFileFactory):
    """Factory para archivos comprimidos (ZIP)"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"archive_{factory.Faker('uuid4')}.zip",
            content=b"PK\x03\x04 fake zip content",
            content_type="application/zip"
        )
    )
    ext_upper = 'ZIP'
    content_type = 'application/zip'
    size_bytes = 5242880


class LargeFileFactory(ProjectFileFactory):
    """Factory para archivos grandes (>100MB)"""
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"large_model_{factory.Faker('uuid4')}.rvt",
            content=b"fake large file content" * 1000,
            content_type="application/octet-stream"
        )
    )
    ext_upper = 'RVT'
    content_type = 'application/octet-stream'
    size_bytes = 125829120


class MaliciousFileFactory(ProjectFileFactory):
    """
    Factory para archivos maliciosos (para tests de seguridad)
    
    SECURITY CRITICAL: Solo para tests. Simula archivos peligrosos.
    """
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name="malicious.exe",
            content=b"MZ fake exe content",
            content_type="application/x-msdownload"
        )
    )
    ext_upper = 'EXE'
    content_type = 'application/x-msdownload'
    size_bytes = 4096


class PathTraversalFileFactory(ProjectFileFactory):
    """
    Factory para archivos con path traversal (para tests de seguridad)
    
    SECURITY CRITICAL: Solo para tests. Simula ataques de path traversal.
    """
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name="../../../etc/passwd",
            content=b"fake malicious content",
            content_type="text/plain"
        )
    )
    ext_upper = ''
    content_type = 'text/plain'
    size_bytes = 256


class ExecutableFileFactory(ProjectFileFactory):
    """
    Factory para archivos ejecutables (para tests de seguridad)
    
    SECURITY CRITICAL: Solo para tests. Simula diferentes tipos de ejecutables.
    """
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name=f"script_{factory.Faker('uuid4')}.sh",
            content=b"#!/bin/bash\necho malicious",
            content_type="application/x-sh"
        )
    )
    ext_upper = 'SH'
    content_type = 'application/x-sh'
    size_bytes = 128


class NoExtensionFileFactory(ProjectFileFactory):
    """
    Factory para archivos sin extensión (edge case)
    
    Edge case: Archivos sin extensión para probar validaciones.
    """
    
    file = factory.LazyAttribute(
        lambda obj: SimpleUploadedFile(
            name="README",
            content=b"file without extension",
            content_type="text/plain"
        )
    )
    ext_upper = ''
    content_type = 'text/plain'
    size_bytes = 256

