# apps/files/storage.py
"""
Storage personalizado para archivos de proyecto.

Desactiva el renombrado automático de Django porque ya lo manejamos
en project_file_path() con el formato legible (1), (2), etc.
"""
import os
import logging

logger = logging.getLogger(__name__)


class NoRenameStorageMixin:
    """
    Mixin que desactiva el renombrado automático de archivos duplicados.
    
    Usamos este mixin porque el renombrado se maneja en project_file_path()
    con un formato más legible: archivo (1).pdf, archivo (2).pdf
    en lugar del formato de Django: archivo_aB3xK9.pdf
    """
    
    def get_valid_name(self, name):
        """
        Retorna el nombre tal cual, sin sanitizarlo.
        
        Django por defecto convierte espacios y paréntesis a underscores.
        Nosotros queremos mantener el formato legible "archivo (1).pdf".
        
        Solo eliminamos caracteres realmente peligrosos para el filesystem.
        """
        # Solo eliminar caracteres que son ilegales en filesystems
        # Windows: \ / : * ? " < > |
        # Unix: / y null byte
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00']
        
        for char in illegal_chars:
            name = name.replace(char, '_')
        
        # No eliminar espacios ni paréntesis - son válidos en todos los filesystems
        return name
    
    def is_name_available(self, name, max_length=None):
        """
        Siempre retorna True para indicar que el nombre está disponible.
        
        Esto evita que Django verifique si el archivo existe en el filesystem
        y lo renombre automáticamente. El manejo de duplicados ya se hizo
        en project_file_path() consultando la base de datos.
        """
        logger.debug(f"is_name_available called with: {name} - returning True (no rename)")
        return True
    
    def get_available_name(self, name, max_length=None):
        """
        Retorna el nombre tal cual, sin modificarlo.
        
        El renombrado para evitar duplicados ya se hizo en
        apps.files.models.project_file_path() antes de llegar aquí.
        
        IMPORTANTE: Django llama a este método con el path completo
        después de upload_to. Debemos retornarlo sin modificar.
        
        Nota: Aunque sobreescribimos is_name_available() para retornar True,
        también sobreescribimos este método por seguridad y para versiones
        anteriores de Django que no usen is_name_available().
        """
        # Log para debugging
        logger.debug(f"get_available_name called with: {name}")
        
        # Retornar el nombre exactamente como viene de upload_to
        # NO verificar si existe, NO renombrar
        return name


# Storage para almacenamiento local (desarrollo)
try:
    from django.core.files.storage import FileSystemStorage
    
    class ProjectFileSystemStorage(NoRenameStorageMixin, FileSystemStorage):
        """Storage local sin renombrado automático."""
        pass
        
except ImportError:
    ProjectFileSystemStorage = None


# Storage para R2/S3 (producción)
try:
    from storages.backends.s3boto3 import S3Boto3Storage
    
    class ProjectS3Storage(NoRenameStorageMixin, S3Boto3Storage):
        """Storage S3/R2 sin renombrado automático."""
        pass
        
except ImportError:
    ProjectS3Storage = None


def get_project_file_storage():
    """
    Retorna el storage apropiado según la configuración.
    """
    import os
    
    if os.environ.get('ENABLE_STORAGES', 'false').lower() == 'true':
        if ProjectS3Storage is not None:
            return ProjectS3Storage()
        else:
            logger.warning("S3Boto3Storage no disponible, usando FileSystemStorage")
    
    if ProjectFileSystemStorage is not None:
        return ProjectFileSystemStorage()
    
    # Fallback al storage por defecto de Django
    from django.core.files.storage import default_storage
    return default_storage
