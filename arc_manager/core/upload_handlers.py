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
            
            # Crear archivo temporal
            self.file = TemporaryUploadedFile(
                name=file_name,
                content_type=content_type,
                size=content_length,
                charset=charset,
                content_type_extra=content_type_extra
            )
            
            # Log para monitoreo
            logger.info(f"📁 Upload handler: Archivo grande {file_name} ({content_length} bytes) - usando disco temporal")
            
        else:
            # Para archivos pequeños, usar memoria (handler por defecto)
            logger.debug(f"📁 Upload handler: Archivo pequeño {file_name} ({content_length} bytes) - usando memoria")
            return super().new_file(field_name, file_name, content_type, content_length, charset, content_type_extra)

    def receive_data_chunk(self, raw_data, start):
        """
        Recibir chunk de datos de forma optimizada
        """
        if hasattr(self, 'file'):
            # Escribir chunk directamente al archivo temporal
            self.file.write(raw_data)
            return None  # No acumular en memoria
        else:
            return super().receive_data_chunk(raw_data, start)

    def file_complete(self, file_size):
        """
        Completar el archivo de forma optimizada
        """
        if hasattr(self, 'file'):
            # Resetear posición del archivo
            self.file.seek(0)
            self.file.size = file_size
            logger.info(f"✅ Upload completado: {self.file.name} ({file_size} bytes)")
            return self.file
        else:
            return super().file_complete(file_size)


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
        logger.debug(f"📊 Progress tracker: Nuevo archivo {file_name} - Total esperado: {self.total_size} bytes")
        
    def receive_data_chunk(self, raw_data, start):
        """
        Actualizar progreso por chunk
        """
        self.uploaded_size += len(raw_data)
        
        # Calcular porcentaje de progreso
        if self.total_size > 0:
            progress = (self.uploaded_size / self.total_size) * 100
            
            # Log cada 10% de progreso para archivos grandes
            if self.total_size > 50 * 1024 * 1024 and progress % 10 == 0:  # >50MB
                logger.info(f"📈 Upload progress: {progress:.1f}% completado")
        
        # No procesar el chunk - dejar que otros handlers lo manejen
        return raw_data

    def upload_complete(self):
        """
        Upload completado
        """
        logger.info(f"🎉 Upload completado: {self.uploaded_size} bytes transferidos")
        return super().upload_complete()
