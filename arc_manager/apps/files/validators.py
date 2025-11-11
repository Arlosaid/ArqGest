# apps/files/validators.py
"""
Validadores de archivos optimizados para producción
"""
import os
import magic
import logging
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class FileValidator:
    """Validador robusto de archivos para producción"""
    
    # MIME types permitidos por extensión
    ALLOWED_MIME_TYPES = {
        'PDF': ['application/pdf', 'application/octet-stream', 'application/x-pdf'],
        'JPG': ['image/jpeg'],
        'JPEG': ['image/jpeg'],
        'PNG': ['image/png'],
        'GIF': ['image/gif'],
        'DWG': ['image/vnd.dwg', 'application/acad', 'application/x-dwg', 'application/octet-stream'],
        'DXF': ['image/vnd.dxf', 'application/dxf', 'application/octet-stream'],
        'RVT': ['application/octet-stream'],  # Archivos Revit
        'SKP': ['application/octet-stream'],  # Archivos SketchUp
        '3DS': ['application/octet-stream'],  # Archivos 3D Studio Max
        'MAX': ['application/octet-stream'],  # Archivos 3D Studio Max
        'ZIP': ['application/zip', 'application/x-zip-compressed', 'application/octet-stream'],
        'RAR': ['application/x-rar-compressed', 'application/vnd.rar', 'application/octet-stream'],
        '7Z': ['application/x-7z-compressed', 'application/octet-stream'],
        'TIFF': ['image/tiff', 'application/octet-stream'],
        'TIF': ['image/tiff', 'application/octet-stream'],
        'DOC': ['application/msword'],
        'DOCX': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'XLS': ['application/vnd.ms-excel'],
        'XLSX': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'PPT': ['application/vnd.ms-powerpoint'],
        'PPTX': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
        'TXT': ['text/plain'],
        'MD': ['text/markdown', 'text/plain'],
    }
    
    # Extensiones peligrosas que nunca se deben permitir
    DANGEROUS_EXTENSIONS = {
        'EXE', 'BAT', 'CMD', 'COM', 'PIF', 'SCR', 'VBS', 'JS', 'JAR',
        'MSI', 'DLL', 'SCF', 'LNK', 'INF', 'REG', 'PS1', 'SH', 'PHP'
    }
    
    def __init__(self, max_size_mb=None, allowed_extensions=None):
        # Siempre usar configuración del sistema para estar actualizado
        if max_size_mb is None:
            try:
                from apps.main.models import SystemSettings
                sys_settings = SystemSettings.load()
                max_size_mb = sys_settings.max_file_size_mb
            except:
                # Fallback si hay error
                max_size_mb = 500
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or set(os.environ.get(
            'ALLOWED_EXTENSIONS', 
            'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,3DS,MAX,ZIP,RAR,7Z,TIFF,DOC,DOCX,XLS,XLSX,PPT,PPTX,TXT,MD'
        ).split(','))
    
    def validate_file(self, uploaded_file, raise_exception=True):
        """
        Validación completa de archivo
        
        Args:
            uploaded_file: Archivo a validar
            raise_exception: Si True, lanza ValidationError. Si False, retorna (is_valid, errors)
        
        Returns:
            Si raise_exception=True: True si válido, lanza ValidationError si no
            Si raise_exception=False: (bool, list) tupla con resultado y lista de errores
        """
        errors = []
        
        # 1. Validar tamaño
        if uploaded_file.size > self.max_size_bytes:
            size_mb = uploaded_file.size / (1024 * 1024)
            max_mb = self.max_size_bytes / (1024 * 1024)
            errors.append(f"Archivo muy grande ({size_mb:.1f}MB, máx: {max_mb}MB)")
        
        # 2. Validar nombre de archivo
        filename_errors = self._validate_filename(uploaded_file.name)
        errors.extend(filename_errors)
        
        # 3. Validar extensión
        extension = self._get_extension(uploaded_file.name)
        if extension in self.DANGEROUS_EXTENSIONS:
            errors.append(f"Tipo de archivo peligroso (.{extension.lower()}) no permitido")
        elif extension not in self.allowed_extensions:
            errors.append(f"Tipo de archivo no permitido (.{extension.lower()})")
        
        # 4. Validar MIME type (si python-magic está disponible)
        try:
            mime_errors = self._validate_mime_type(uploaded_file, extension)
            errors.extend(mime_errors)
        except Exception as e:
            logger.warning(f"No se pudo validar MIME type: {e}")
        
        # 5. Validar contenido básico
        content_errors = self._validate_content(uploaded_file)
        errors.extend(content_errors)
        
        if errors:
            if raise_exception:
                raise ValidationError(errors)
            else:
                return (False, errors)
        
        if raise_exception:
            return True
        else:
            return (True, [])
    
    def _validate_filename(self, filename):
        """Validar nombre de archivo"""
        errors = []
        
        if len(filename) > 255:
            errors.append("Nombre de archivo muy largo (máx: 255 caracteres)")
        
        # Caracteres peligrosos
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00', '..', '\\']
        found_chars = [char for char in dangerous_chars if char in filename]
        if found_chars:
            errors.append(f"Nombre contiene caracteres no permitidos: {found_chars}")
        
        # Nombres reservados en Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
            'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            errors.append(f"Nombre de archivo reservado: {name_without_ext}")
        
        return errors
    
    def _get_extension(self, filename):
        """Obtener extensión del archivo"""
        return os.path.splitext(filename)[1].replace('.', '').upper()
    
    def _validate_mime_type(self, uploaded_file, extension):
        """Validar MIME type contra extensión"""
        errors = []
        
        try:
            # Leer primeros bytes para detectar MIME type
            uploaded_file.seek(0)
            file_header = uploaded_file.read(2048)
            uploaded_file.seek(0)
            
            # Usar python-magic si está disponible
            if hasattr(magic, 'from_buffer'):
                detected_mime = magic.from_buffer(file_header, mime=True)
                
                allowed_mimes = self.ALLOWED_MIME_TYPES.get(extension, [])
                if allowed_mimes and detected_mime not in allowed_mimes:
                    # Algunos casos especiales donde el MIME puede variar
                    if not self._is_mime_acceptable(detected_mime, extension):
                        errors.append(
                            f"Contenido del archivo no coincide con extensión "
                            f"(.{extension.lower()}). Detectado: {detected_mime}"
                        )
            
        except Exception as e:
            logger.warning(f"Error validando MIME type: {e}")
        
        return errors
    
    def _is_mime_acceptable(self, detected_mime, extension):
        """Casos especiales donde MIME puede variar"""
        # 🔥 FIX: Muchos archivos binarios legítimos se detectan como application/octet-stream
        # Esto es NORMAL y NO debe rechazarse
        if detected_mime == 'application/octet-stream':
            # Archivos de arquitectura/diseño que usan formatos binarios propietarios
            if extension in ['DWG', 'DXF', 'RVT', 'SKP', '3DS', 'MAX']:
                return True
            
            # Archivos comprimidos (ZIP, RAR, 7Z) pueden detectarse como octet-stream
            if extension in ['ZIP', 'RAR', '7Z']:
                return True
            
            # Archivos de imagen TIFF (común en arquitectura)
            if extension in ['TIFF', 'TIF']:
                return True
            
            # 🔥 FIX: Archivos PDF pueden detectarse como octet-stream en algunos casos
            if extension == 'PDF':
                return True
        
        # Archivos PDF pueden tener diferentes MIME types dependiendo del creador
        if extension == 'PDF':
            # Aceptar cualquier MIME type que contenga 'pdf' o sea application/octet-stream
            if 'pdf' in detected_mime.lower() or detected_mime == 'application/octet-stream':
                return True
        
        # Archivos de texto pueden detectarse como diferentes tipos
        if extension in ['TXT', 'MD'] and detected_mime.startswith('text/'):
            return True
        
        # Imágenes pueden tener variaciones en el MIME type
        if extension in ['JPG', 'JPEG'] and detected_mime in ['image/jpeg', 'image/jpg']:
            return True
        
        # PDFs a veces se detectan con variaciones
        if extension == 'PDF' and 'pdf' in detected_mime.lower():
            return True
        
        return False
    
    def _validate_content(self, uploaded_file):
        """Validaciones básicas de contenido"""
        errors = []
        
        # Verificar que no esté vacío
        if uploaded_file.size == 0:
            errors.append("Archivo vacío")
        elif uploaded_file.size < 10:
            # Solo rechazar archivos extremadamente pequeños en extensiones que deberían ser más grandes
            extension = self._get_extension(uploaded_file.name)
            # Archivos que típicamente son más grandes
            if extension in ['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX']:
                errors.append("Archivo sospechosamente pequeño (posiblemente corrupto)")
        
        # Verificar que se pueda leer
        try:
            uploaded_file.seek(0)
            first_bytes = uploaded_file.read(100)
            uploaded_file.seek(0)
            
            # Verificar que no sea un archivo de script ejecutable
            if first_bytes.startswith((b'#!/', b'@echo', b'<script')):
                errors.append("Contenido de script no permitido")
            
            # SECURITY: Detectar magic bytes de ejecutables Windows (MZ header)
            if first_bytes.startswith(b'MZ'):
                errors.append("Contenido sospechoso: archivo ejecutable detectado")
            
            # SECURITY: Detectar magic bytes de ejecutables ELF (Linux)
            if first_bytes.startswith(b'\x7fELF'):
                errors.append("Contenido sospechoso: ejecutable Linux detectado")
            
        except Exception as e:
            errors.append(f"Error leyendo contenido del archivo: {e}")
        
        return errors


def validate_project_file(uploaded_file):
    """
    Función de validación principal para archivos de proyecto
    """
    validator = FileValidator()
    return validator.validate_file(uploaded_file)


def validate_file_size(uploaded_file, max_size_mb=None):
    """Validar solo el tamaño del archivo"""
    if max_size_mb is None:
        try:
            from apps.main.models import SystemSettings
            sys_settings = SystemSettings.load()
            max_size_mb = sys_settings.max_file_size_mb
        except:
            max_size_mb = 500  # Fallback
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if uploaded_file.size > max_size_bytes:
        size_mb = uploaded_file.size / (1024 * 1024)
        raise ValidationError(
            f"Archivo muy grande ({size_mb:.1f}MB, máximo permitido: {max_size_mb}MB)"
        )


def validate_file_extension(filename, allowed_extensions=None):
    """Validar solo la extensión del archivo"""
    if allowed_extensions is None:
        allowed_extensions = set(os.environ.get(
            'ALLOWED_EXTENSIONS',
            'PDF,JPG,JPEG,PNG,GIF,DWG,DXF,RVT,SKP,3DS,MAX,ZIP,RAR,7Z,TIFF,DOC,DOCX,XLS,XLSX,PPT,PPTX,TXT,MD'
        ).split(','))
    
    extension = os.path.splitext(filename)[1].replace('.', '').upper()
    
    # Verificar extensiones peligrosas
    if extension in FileValidator.DANGEROUS_EXTENSIONS:
        raise ValidationError(f"Tipo de archivo peligroso (.{extension.lower()}) no permitido")
    
    if extension not in allowed_extensions:
        raise ValidationError(f"Tipo de archivo no permitido (.{extension.lower()})")
