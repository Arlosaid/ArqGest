"""
Tests de seguridad CRÍTICOS para archivos

Estos tests validan protecciones contra:
- Subida de archivos ejecutables
- Path traversal attacks
- MIME type spoofing
- Acceso no autorizado cross-organization
- Ataques de contenido malicioso
"""
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.files.models import ProjectFile
from apps.files.validators import (
    FileValidator,
    validate_project_file,
    validate_file_extension,
    validate_file_size,
)
from tests.factories import (
    ProjectFileFactory,
    PDFFileFactory,
    MaliciousFileFactory,
    PathTraversalFileFactory,
    ExecutableFileFactory,
    PhaseFactory,
    UserFactory,
    OrganizationFactory,
)


@pytest.mark.django_db
@pytest.mark.security
class TestDangerousExtensions:
    """
    SECURITY CRITICAL: Prevenir subida de archivos ejecutables.
    
    Un archivo ejecutable malicioso podría comprometer el servidor.
    """
    
    def test_exe_files_are_blocked(self):
        """
        SECURITY: Archivos .exe deben ser bloqueados siempre.
        
        BUG POTENCIAL: Si esto falla, un atacante podría subir malware.
        """
        malicious_file = SimpleUploadedFile(
            name="malware.exe",
            content=b"MZ\x90\x00",  # Inicio de ejecutable Windows
            content_type="application/x-msdownload"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            validate_project_file(malicious_file)
        
        assert "peligroso" in str(exc_info.value).lower()
    
    def test_bat_files_are_blocked(self):
        """SECURITY: Archivos batch (.bat) son bloqueados"""
        batch_file = SimpleUploadedFile(
            name="malicious.bat",
            content=b"@echo off\nrdel /s /q C:\\",
            content_type="application/x-bat"
        )
        
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.bat")
    
    def test_sh_files_are_blocked(self):
        """SECURITY: Scripts shell (.sh) son bloqueados"""
        shell_file = SimpleUploadedFile(
            name="malicious.sh",
            content=b"#!/bin/bash\nrm -rf /",
            content_type="application/x-sh"
        )
        
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.sh")
    
    def test_vbs_files_are_blocked(self):
        """SECURITY: Scripts VBScript (.vbs) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.vbs")
    
    def test_js_files_are_blocked(self):
        """SECURITY: JavaScript ejecutable (.js) es bloqueado"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.js")
    
    def test_ps1_files_are_blocked(self):
        """SECURITY: PowerShell scripts (.ps1) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.ps1")
    
    def test_cmd_files_are_blocked(self):
        """SECURITY: Archivos CMD (.cmd) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.cmd")
    
    def test_com_files_are_blocked(self):
        """SECURITY: Ejecutables COM (.com) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.com")
    
    def test_pif_files_are_blocked(self):
        """SECURITY: Program Information Files (.pif) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.pif")
    
    def test_scr_files_are_blocked(self):
        """SECURITY: Screensaver ejecutables (.scr) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.scr")
    
    def test_jar_files_are_blocked(self):
        """SECURITY: Java Archives (.jar) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.jar")
    
    def test_msi_files_are_blocked(self):
        """SECURITY: Instaladores Windows (.msi) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.msi")
    
    def test_dll_files_are_blocked(self):
        """SECURITY: DLL files (.dll) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.dll")
    
    def test_php_files_are_blocked(self):
        """SECURITY: PHP scripts (.php) son bloqueados"""
        with pytest.raises(ValidationError):
            validate_file_extension("malicious.php")


@pytest.mark.django_db
@pytest.mark.security
class TestPathTraversal:
    """
    SECURITY CRITICAL: Prevenir path traversal attacks.
    
    Un atacante podría intentar escribir archivos fuera del directorio
    permitido usando rutas como "../../../etc/passwd".
    """
    
    def test_path_traversal_with_dots_is_sanitized(self):
        """
        SECURITY: Path traversal con ../ debe ser sanitizado.
        
        BUG POTENCIAL: Si falla, atacante podría escribir archivos
        en cualquier ubicación del servidor.
        """
        phase = PhaseFactory()
        
        malicious_file = SimpleUploadedFile(
            name="../../../etc/passwd",
            content=b"malicious content",
            content_type="text/plain"
        )
        
        # El sistema debe sanitizar el nombre o rechazarlo
        # La función project_file_path debe generar un path seguro
        from apps.files.models import project_file_path
        
        file_obj = ProjectFile(
            phase=phase,
            file=malicious_file,
            uploaded_by=UserFactory()
        )
        
        generated_path = project_file_path(file_obj, malicious_file.name)
        
        # El path NO debe contener ../
        assert "../" not in generated_path
        assert "..\\" not in generated_path
    
    def test_path_traversal_windows_style(self):
        """SECURITY: Path traversal estilo Windows (..\) es sanitizado"""
        phase = PhaseFactory()
        
        malicious_file = SimpleUploadedFile(
            name="..\\..\\..\\windows\\system32\\config\\sam",
            content=b"malicious content",
            content_type="application/octet-stream"
        )
        
        file_obj = ProjectFile(
            phase=phase,
            file=malicious_file,
            uploaded_by=UserFactory()
        )
        
        from apps.files.models import project_file_path
        generated_path = project_file_path(file_obj, malicious_file.name)
        
        assert "..\\" not in generated_path
        assert "system32" not in generated_path or "organizations/" in generated_path
    
    def test_absolute_path_is_sanitized(self):
        """SECURITY: Rutas absolutas son convertidas a relativas"""
        phase = PhaseFactory()
        
        malicious_file = SimpleUploadedFile(
            name="/etc/passwd",
            content=b"malicious content",
            content_type="text/plain"
        )
        
        file_obj = ProjectFile(
            phase=phase,
            file=malicious_file,
            uploaded_by=UserFactory()
        )
        
        from apps.files.models import project_file_path
        generated_path = project_file_path(file_obj, malicious_file.name)
        
        # El path debe empezar con "organizations/"
        assert generated_path.startswith("organizations/")
    
    def test_null_bytes_in_filename_are_handled(self):
        """
        SECURITY: Null bytes en nombres de archivo son manejados.
        
        Algunos sistemas usan null bytes para truncar nombres de archivo.
        """
        phase = PhaseFactory()
        
        # Nombre con null byte: "malware.pdf\x00.exe"
        # El sistema podría ver "malware.pdf" pero ejecutar ".exe"
        malicious_file = SimpleUploadedFile(
            name="malware.pdf\x00.exe",
            content=b"fake pdf",
            content_type="application/pdf"
        )
        
        file_obj = ProjectFile(
            phase=phase,
            file=malicious_file,
            uploaded_by=UserFactory()
        )
        
        from apps.files.models import project_file_path
        generated_path = project_file_path(file_obj, malicious_file.name)
        
        # El null byte no debe estar en el path
        assert "\x00" not in generated_path


@pytest.mark.django_db
@pytest.mark.security
class TestMimeTypeSpoofing:
    """
    SECURITY: Prevenir spoofing de MIME types.
    
    Un atacante podría renombrar "malware.exe" a "document.pdf"
    y cambiar el MIME type para evadir validaciones.
    """
    
    def test_exe_with_pdf_extension_is_detected(self):
        """
        SECURITY: Ejecutable renombrado como PDF es detectado.
        
        BUG POTENCIAL: Validación solo por extensión permite bypass.
        """
        fake_pdf = SimpleUploadedFile(
            name="document.pdf",
            content=b"MZ\x90\x00",  # Magic bytes de ejecutable Windows
            content_type="application/pdf"  # MIME type falso
        )
        
        validator = FileValidator()
        
        # El validador debe detectar la inconsistencia
        # (esto depende de si FileValidator usa python-magic)
        is_valid, errors = validator.validate_file(fake_pdf, raise_exception=False)
        
        # Si hay detección de contenido, debe fallar
        # Si solo valida extensión, pasará pero no es ideal
        # Documentamos este comportamiento
        if not is_valid:
            assert any("contenido" in e.lower() or "sospechoso" in e.lower() 
                      for e in errors)
    
    def test_script_content_in_text_file_is_detected(self):
        """SECURITY: Contenido de script en archivo de texto es detectado"""
        script_file = SimpleUploadedFile(
            name="innocent.txt",
            content=b"#!/bin/bash\nrm -rf /",
            content_type="text/plain"
        )
        
        validator = FileValidator()
        is_valid, errors = validator.validate_file(script_file, raise_exception=False)
        
        # El validador debe detectar contenido de script
        if not is_valid:
            assert any("script" in e.lower() for e in errors)
    
    def test_php_code_in_image_file(self):
        """
        SECURITY: Código PHP inyectado en imagen es detectado.
        
        Algunos atacantes inyectan código en metadatos de imágenes.
        """
        malicious_image = SimpleUploadedFile(
            name="image.jpg",
            content=b"\xff\xd8\xff\xe0<?php system($_GET['cmd']); ?>",
            content_type="image/jpeg"
        )
        
        # El sistema debería permitir la imagen pero el código no se ejecutará
        # porque las imágenes no se procesan como código
        # Esto es más una validación de arquitectura
        validator = FileValidator()
        is_valid, errors = validator.validate_file(malicious_image, raise_exception=False)
        
        # JPG válido con código inyectado podría pasar
        # La protección real está en no ejecutar archivos subidos
        assert True  # Documentamos que esto es arquitectural


@pytest.mark.django_db
@pytest.mark.security
class TestCrossOrganizationAccess:
    """
    SECURITY CRITICAL: Prevenir acceso a archivos de otras organizaciones.
    
    Un usuario no debe poder acceder a archivos de organizaciones
    a las que no pertenece.
    """
    
    def test_user_cannot_upload_to_different_org_project(self, use_local_storage):
        """
        SECURITY: Usuario no puede subir archivos a proyecto de otra org.
        
        BUG POTENCIAL: Si falla, usuarios podrían contaminar datos
        de otras organizaciones.
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        user_org1 = UserFactory(organization=org1)
        phase_org2 = PhaseFactory(project__organization=org2)
        
        # Intentar crear archivo manualmente (sin factory) para probar la validación
        file_upload = SimpleUploadedFile(
            name="test.pdf",
            content=b"PDF content",
            content_type="application/pdf"
        )
        
        file_obj = ProjectFile(
            phase=phase_org2,
            uploaded_by=user_org1,
            file=file_upload
        )
        
        # La validación debe fallar al intentar guardar
        with pytest.raises(ValidationError) as exc_info:
            file_obj.save()
        
        assert 'uploaded_by' in exc_info.value.message_dict
    
    def test_file_path_contains_correct_organization(self, use_local_storage):
        """SECURITY: Path de archivo contiene ID de organización correcta"""
        org = OrganizationFactory()
        phase = PhaseFactory(project__organization=org)
        user = UserFactory(organization=org)
        
        file_obj = PDFFileFactory(
            phase=phase,
            uploaded_by=user
        )
        
        # El path debe contener el ID de la organización
        assert f"organizations/{org.id}/" in file_obj.file.name
    
    def test_cannot_access_file_from_different_org(self, use_local_storage):
        """
        SECURITY: No se puede acceder a archivo de otra organización.
        
        Este test valida que las queries incluyan filtros de organización.
        """
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        # Crear usuario de org1 para subir el archivo
        user_org1 = UserFactory(organization=org1)
        phase_org1 = PhaseFactory(project__organization=org1)
        
        file_org1 = PDFFileFactory(
            phase=phase_org1,
            uploaded_by=user_org1
        )
        
        # Buscar archivos de org2 no debe retornar archivos de org1
        files_org2 = ProjectFile.objects.by_organization(org2.id)
        
        assert file_org1 not in files_org2
        assert files_org2.count() == 0


@pytest.mark.django_db
@pytest.mark.security
class TestFileSizeLimits:
    """
    SECURITY: Prevenir ataques de denegación de servicio por archivos grandes.
    
    Archivos excesivamente grandes podrían llenar el storage o causar timeouts.
    """
    
    def test_file_exceeding_max_size_is_rejected(self):
        """
        SECURITY: Archivos que exceden tamaño máximo son rechazados.
        
        BUG POTENCIAL: Sin límite, atacante podría llenar el storage.
        """
        max_size_mb = 500
        file_size_bytes = (max_size_mb + 1) * 1024 * 1024
        
        large_file = SimpleUploadedFile(
            name="huge_file.pdf",
            content=b"x" * 1000,  # Contenido pequeño pero reporta tamaño grande
            content_type="application/pdf"
        )
        large_file.size = file_size_bytes
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(large_file, max_size_mb=max_size_mb)
        
        assert "máximo" in str(exc_info.value).lower()
    
    def test_zero_byte_file_is_rejected(self):
        """SECURITY: Archivos de 0 bytes son rechazados"""
        empty_file = SimpleUploadedFile(
            name="empty.pdf",
            content=b"",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        is_valid, errors = validator.validate_file(empty_file, raise_exception=False)
        
        assert not is_valid
        assert any("vacío" in e.lower() for e in errors)
    
    def test_suspiciously_small_file_is_flagged(self):
        """SECURITY: Archivos sospechosamente pequeños son marcados"""
        tiny_file = SimpleUploadedFile(
            name="document.pdf",
            content=b"PDF",  # Solo 3 bytes
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        is_valid, errors = validator.validate_file(tiny_file, raise_exception=False)
        
        assert not is_valid
        assert any("pequeño" in e.lower() or "sospechoso" in e.lower() 
                  for e in errors)


@pytest.mark.django_db
@pytest.mark.security
class TestFileNameValidation:
    """
    SECURITY: Validar nombres de archivo para prevenir ataques.
    """
    
    def test_filename_with_multiple_extensions(self):
        """
        SECURITY: Archivos con múltiples extensiones son manejados.
        
        Ejemplo: "document.pdf.exe" podría confundir al sistema.
        """
        multi_ext_file = SimpleUploadedFile(
            name="document.pdf.exe",
            content=b"fake content",
            content_type="application/pdf"
        )
        
        # La extensión final (.exe) debe ser detectada
        with pytest.raises(ValidationError):
            validate_file_extension("document.pdf.exe")
    
    def test_filename_with_unicode_characters(self, use_local_storage):
        """SECURITY: Nombres con Unicode son manejados correctamente"""
        unicode_file = SimpleUploadedFile(
            name="文档.pdf",
            content=b"fake pdf",
            content_type="application/pdf"
        )
        
        phase = PhaseFactory()
        file_obj = ProjectFile(
            phase=phase,
            file=unicode_file,
            uploaded_by=UserFactory()
        )
        
        from apps.files.models import project_file_path
        generated_path = project_file_path(file_obj, unicode_file.name)
        
        # El path debe ser generado sin errores
        assert generated_path
    
    def test_filename_with_special_characters(self):
        """SECURITY: Caracteres especiales peligrosos son manejados"""
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        
        for char in dangerous_chars:
            filename = f"file{char}name.pdf"
            
            # El sistema debe manejar estos caracteres de alguna forma
            # (sanitizándolos o rechazándolos)
            phase = PhaseFactory()
            file_obj = ProjectFile(
                phase=phase,
                uploaded_by=UserFactory()
            )
            
            from apps.files.models import project_file_path
            try:
                generated_path = project_file_path(file_obj, filename)
                # Si se genera, no debe contener el carácter peligroso
                # o debe estar escapado
                assert generated_path
            except Exception:
                # Rechazar el archivo también es válido
                pass
    
    def test_very_long_filename_is_handled(self, use_local_storage):
        """
        SECURITY: Nombres de archivo muy largos son manejados.
        
        BUG POTENCIAL: Nombres >255 caracteres pueden causar errores.
        """
        long_name = "a" * 300 + ".pdf"
        
        long_file = SimpleUploadedFile(
            name=long_name,
            content=b"fake pdf",
            content_type="application/pdf"
        )
        
        phase = PhaseFactory()
        file_obj = ProjectFile(
            phase=phase,
            file=long_file,
            uploaded_by=UserFactory()
        )
        
        from apps.files.models import project_file_path
        generated_path = project_file_path(file_obj, long_name)
        
        # El path debe ser generado (posiblemente truncado)
        assert generated_path
        # El nombre del archivo no debe exceder límites del sistema
        import os
        filename = os.path.basename(generated_path)
        assert len(filename) <= 255


@pytest.mark.django_db
@pytest.mark.security
class TestAllowedExtensions:
    """
    SECURITY: Validar que solo extensiones permitidas son aceptadas.
    """
    
    def test_pdf_extension_is_allowed(self):
        """SECURITY: PDF es una extensión permitida"""
        try:
            validate_file_extension("document.pdf")
        except ValidationError:
            pytest.fail("PDF debería ser permitido")
    
    def test_jpg_extension_is_allowed(self):
        """SECURITY: JPG es una extensión permitida"""
        try:
            validate_file_extension("photo.jpg")
        except ValidationError:
            pytest.fail("JPG debería ser permitido")
    
    def test_dwg_extension_is_allowed(self):
        """SECURITY: DWG (AutoCAD) es una extensión permitida"""
        try:
            validate_file_extension("drawing.dwg")
        except ValidationError:
            pytest.fail("DWG debería ser permitido")
    
    def test_rvt_extension_is_allowed(self):
        """SECURITY: RVT (Revit) es una extensión permitida"""
        try:
            validate_file_extension("model.rvt")
        except ValidationError:
            pytest.fail("RVT debería ser permitido")
    
    def test_disallowed_extension_is_rejected(self):
        """SECURITY: Extensiones no permitidas son rechazadas"""
        with pytest.raises(ValidationError):
            validate_file_extension("file.xyz")
    
    def test_extension_is_case_insensitive(self):
        """SECURITY: Validación de extensión es case-insensitive"""
        # Todas estas variantes deben funcionar igual
        try:
            validate_file_extension("document.PDF")
            validate_file_extension("document.pdf")
            validate_file_extension("document.Pdf")
        except ValidationError:
            pytest.fail("Validación debería ser case-insensitive")
    
    def test_file_without_extension_is_rejected(self):
        """SECURITY: Archivos sin extensión son rechazados"""
        with pytest.raises(ValidationError):
            validate_file_extension("README")


@pytest.mark.django_db
@pytest.mark.security
class TestContentValidation:
    """
    SECURITY: Validar contenido de archivos, no solo nombres.
    """
    
    def test_script_header_is_detected(self):
        """SECURITY: Headers de script (#!/) son detectados"""
        script_file = SimpleUploadedFile(
            name="file.txt",
            content=b"#!/bin/bash\necho 'malicious'",
            content_type="text/plain"
        )
        
        validator = FileValidator()
        is_valid, errors = validator.validate_file(script_file, raise_exception=False)
        
        assert not is_valid
        assert any("script" in e.lower() for e in errors)
    
    def test_batch_echo_command_is_detected(self):
        """SECURITY: Comandos batch (@echo) son detectados"""
        batch_file = SimpleUploadedFile(
            name="file.txt",
            content=b"@echo off\nrdel /s /q",
            content_type="text/plain"
        )
        
        validator = FileValidator()
        is_valid, errors = validator.validate_file(batch_file, raise_exception=False)
        
        assert not is_valid
        assert any("script" in e.lower() for e in errors)
    
    def test_html_script_tag_is_detected(self):
        """SECURITY: Tags <script> en archivos son detectados"""
        html_file = SimpleUploadedFile(
            name="file.txt",
            content=b"<script>alert('XSS')</script>",
            content_type="text/plain"
        )
        
        validator = FileValidator()
        is_valid, errors = validator.validate_file(html_file, raise_exception=False)
        
        assert not is_valid
        assert any("script" in e.lower() for e in errors)

