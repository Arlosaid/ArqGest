"""
🚀 Upload Handlers Optimizados para Rendimiento del Servidor
Maneja uploads grandes sin saturar la memoria del servidor
"""
import os
import tempfile
from django.core.files.uploadhandler import TemporaryFileUploadHandler, FileUploadHandler
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class OptimizedTemporaryFileUploadHandler(TemporaryFileUploadHandler):
    """
    Upload handler optimizado que:
    1. Escribe archivos grandes directamente a disco
    2. Usa streaming para reducir uso de memoria
    3. Proporciona mejor control de recursos
    """
    
    def __init__(self, request=None):
        super().__init__(request)
        self.chunk_size = 64 * 1024  # 64KB chunks para streaming eficiente
        
    def new_file(self, field_name, file_name, content_type, content_length, charset=None, content_type_extra=None):
        """
        Crear nuevo archivo temporal optimizado
        """
        # Solo usar archivo temporal para archivos grandes (>25MB)
        if content_length and content_length > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
            # Crear directorio temporal si no existe
            temp_dir = getattr(settings, 'FILE_UPLOAD_TEMP_DIR', None)
            if temp_dir and not os.path.exists(temp_dir):
                try:
                    os.makedirs(temp_dir, mode=0o755, exist_ok=True)
                except OSError as e:
                    logger.warning(f"No se pudo crear directorio temporal {temp_dir}: {e}")
                    temp_dir = None
            
            # Crear archivo temporal con directorio específico si está disponible
            if temp_dir:
                self.file = TemporaryUploadedFile(
                    name=file_name,
                    content_type=content_type,
                    size=0,  # Se actualizará en file_complete
                    charset=charset,
                    content_type_extra=content_type_extra
                )
            else:
                # Usar directorio temporal del sistema
                self.file = TemporaryUploadedFile(
                    name=file_name,
                    content_type=content_type,
                    size=0,
                    charset=charset,
                    content_type_extra=content_type_extra
                )
        else:
            # Para archivos pequeños, usar memoria (handler por defecto)
            # No manejar archivos pequeños en este handler, dejar al MemoryFileUploadHandler
            return super().new_file(field_name, file_name, content_type, content_length, charset, content_type_extra)

    def receive_data_chunk(self, raw_data, start):
        """
        Recibir chunk de datos de forma optimizada
        """
        if hasattr(self, 'file') and self.file is not None:
            # Escribir chunk directamente al archivo temporal
            try:
                self.file.write(raw_data)
                # 🔥 CRÍTICO: Retornar None para indicar que manejamos el chunk
                # Django no acumulará esto en memoria
                return None
            except Exception as e:
                logger.error(f"Error writing chunk to temporary file: {e}")
                # Si falla, dejar que Django lo maneje
                return raw_data
        else:
            # No tenemos archivo, dejar que otro handler lo maneje
            return raw_data

    def file_complete(self, file_size):
        """
        Completar el archivo de forma optimizada
        """
        if hasattr(self, 'file') and self.file is not None:
            try:
                # 🔥 CRÍTICO: Asegurar que el archivo se cierre y se resetee correctamente
                # Flush para asegurar que todo se escribió a disco
                if hasattr(self.file, 'flush'):
                    self.file.flush()
                
                # Resetear posición del archivo para que Django pueda leerlo
                self.file.seek(0)
                
                # Actualizar tamaño del archivo
                self.file.size = file_size
                
                # Log de éxito con detalles
                logger.info(
                    f"Upload completed: {self.file.name} "
                    f"({file_size/(1024*1024):.2f} MB)"
                )
                
                # Verificar que el archivo temporal existe y tiene contenido
                if hasattr(self.file, 'temporary_file_path'):
                    temp_path = self.file.temporary_file_path()
                    if os.path.exists(temp_path):
                        actual_size = os.path.getsize(temp_path)
                        if actual_size != file_size:
                            logger.warning(
                                f"File size mismatch: disk ({actual_size}) differs from expected ({file_size})"
                            )
                        else:
                            logger.debug(f"Temporary file verified: {temp_path}")
                    else:
                        logger.error(f"Temporary file not found: {temp_path}")
                
                return self.file
                
            except Exception as e:
                logger.error(f"Error completing file upload: {e}", exc_info=True)
                # Intentar retornar el archivo de todos modos
                return self.file if hasattr(self, 'file') else None
        else:
            # No manejamos este archivo, dejar que otro handler lo complete
            return None


class ProgressTrackingUploadHandler(FileUploadHandler):
    """
    Handler para tracking de progreso en tiempo real
    (Opcional - para futuras mejoras con WebSockets)
    """
    
    def __init__(self, request=None):
        super().__init__(request)
        self.total_size = 0
        self.uploaded_size = 0
        
    def new_file(self, field_name, file_name, content_type, content_length, charset=None, content_type_extra=None):
        """
        Inicializar tracking de progreso
        """
        self.total_size += content_length or 0
        logger.debug(f"Progress tracker: New file {file_name} - Expected size: {self.total_size} bytes")
        
    def receive_data_chunk(self, raw_data, start):
        """
        Actualizar progreso por chunk
        """
        self.uploaded_size += len(raw_data)
        
        # Calcular porcentaje de progreso
        if self.total_size > 0:
            progress = (self.uploaded_size / self.total_size) * 100
            
            # Log solo cada 25% de progreso para archivos grandes (reducir ruido)
            # Solo loguear cuando hay problemas o milestones importantes
            if self.total_size > 100 * 1024 * 1024 and progress >= 25 and progress % 25 < 1:  # >100MB
                logger.debug(f"Upload progress: {progress:.1f}% completado")
        
        # No procesar el chunk - dejar que otros handlers lo manejen
        return raw_data

    def upload_complete(self):
        """
        Upload completado
        """
        # Log cambiado a DEBUG - solo interesa en desarrollo
        logger.debug(f"Upload completado: {self.uploaded_size} bytes transferidos")
        return super().upload_complete()
