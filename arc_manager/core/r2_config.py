# core/r2_config.py
"""
Configuración optimizada para Cloudflare R2 con archivos grandes
"""
import os
import boto3
from botocore.config import Config
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_optimized_r2_client():
    """
    Cliente R2 optimizado para archivos grandes de arquitectura
    """
    if not getattr(settings, 'AWS_S3_ENDPOINT_URL', None):
        raise ValueError("R2 no está configurado. Falta AWS_S3_ENDPOINT_URL")
    
    # CONFIGURACIÓN ULTRA-OPTIMIZADA para máximo rendimiento
    config = Config(
        # Timeouts ultra-extendidos para archivos masivos
        connect_timeout=120,  # 2 minutos para conectar (redes lentas/saturadas)
        read_timeout=1800,    # 30 minutos para archivos masivos
        
        # Sistema de retry ultra-robusto
        retries={
            'max_attempts': 5,
            'mode': 'adaptive',  # Retry inteligente basado en el tipo de error
            'total_max_attempts': 10,  # Máximo absoluto de intentos
            'backoff': {
                'base': 2,  # Backoff exponencial base
                'max_value': 120  # Máximo 2 minutos entre retries
            }
        },
        
        # Configuración multipart ultra-optimizada para arquitectos
        s3={
            'multipart_threshold': 25 * 1024 * 1024,  # 25MB - iniciar multipart
            'multipart_chunksize': 50 * 1024 * 1024,  # 50MB por chunk (menos overhead)
            'max_concurrency': 15,  # 15 conexiones concurrentes (máximo paralelismo)
            'max_io_queue': 1000,   # Cola I/O masiva para archivos grandes
            'use_threads': True,     # Threading completo
            'max_bandwidth': None,   # Sin límites de ancho de banda
        },
        
        # Pool de conexiones optimizado
        max_pool_connections=50,  # 50 conexiones en pool
        
        # Configuración de región optimizada
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'auto'),
        
        # Signature v4 para máxima compatibilidad
        signature_version='s3v4',
        
        # Optimizaciones específicas para R2
        parameter_validation=False,  # Sin validación estricta (mejor performance)
        tcp_keepalive=True,  # Mantener conexiones TCP vivas
        
        # Headers de performance
        user_agent_extra='ArcManager/OptimizedR2Client',
    )
    
    try:
        client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=config
        )
        
        # Verificar conectividad
        client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        
        logger.info(f"R2 client configured: {settings.AWS_S3_ENDPOINT_URL}")
        return client
        
    except Exception as e:
        logger.error(f"Error configuring R2 client: {e}")
        raise


def test_r2_large_file_upload():
    """
    Test de configuración para archivos grandes en R2
    """
    try:
        client = get_optimized_r2_client()
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        
        # Test de configuración multipart
        response = client.list_multipart_uploads(Bucket=bucket)
        
        logger.info("R2 configured for large files")
        return True, "Configuración R2 OK"
        
    except Exception as e:
        logger.error(f"Error in R2 test: {e}")
        return False, str(e)


def get_r2_upload_limits():
    """
    Obtener límites actuales de R2
    """
    return {
        'max_file_size': '5TB',  # Límite de R2
        'multipart_threshold': '25MB',
        'multipart_chunksize': '25MB', 
        'max_concurrency': 10,
        'connect_timeout': '60s',
        'read_timeout': '15min',
        'max_retries': 3,
        'presign_expires': '2h'
    }


def optimize_r2_for_architecture_files():
    """
    Configuración específica para archivos de arquitectura
    """
    recommendations = {
        'file_types': {
            'dwg': 'Usar compresión ZIP para múltiples archivos DWG',
            'rvt': 'Subir directamente - R2 maneja archivos grandes nativamente',
            'skp': 'Óptimo para R2 - sin modificaciones necesarias',
            '3ds': 'Considerar compresión para proyectos con muchos assets',
            'renders': 'Usar formatos optimizados (WebP para web, PNG para calidad)'
        },
        
        'upload_strategies': {
            'single_large_file': 'Usar multipart automático (>25MB)',
            'multiple_files': 'Upload secuencial para evitar saturar conexión',
            'project_packages': 'Comprimir proyecto completo en ZIP/7Z'
        },
        
        'performance_tips': {
            'connection': 'Usar conexión estable para archivos >100MB',
            'retry': 'Sistema de retry automático configurado',
            'progress': 'Tracking de progreso disponible via HTMX',
            'validation': 'Validación previa antes del upload a R2'
        }
    }
    
    return recommendations


class R2HealthCheck:
    """
    Monitor de salud para R2
    """
    
    @staticmethod
    def check_connectivity():
        """Verificar conectividad básica"""
        try:
            client = get_optimized_r2_client()
            client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            return True, "Conectividad OK"
        except Exception as e:
            return False, f"Error de conectividad: {e}"
    
    @staticmethod
    def check_upload_capability():
        """Verificar capacidad de upload"""
        try:
            client = get_optimized_r2_client()
            
            # Test con archivo pequeño
            test_key = 'health-check/test.txt'
            client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key,
                Body=b'health check test'
            )
            
            # Limpiar test
            client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key
            )
            
            return True, "Upload capability OK"
            
        except Exception as e:
            return False, f"Error de upload: {e}"
    
    @staticmethod
    def check_multipart_capability():
        """Verificar capacidad multipart"""
        try:
            client = get_optimized_r2_client()
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            
            # Iniciar multipart upload de test
            test_key = 'health-check/multipart-test.bin'
            response = client.create_multipart_upload(
                Bucket=bucket,
                Key=test_key
            )
            
            upload_id = response['UploadId']
            
            # Cancelar el multipart upload
            client.abort_multipart_upload(
                Bucket=bucket,
                Key=test_key,
                UploadId=upload_id
            )
            
            return True, "Multipart capability OK"
            
        except Exception as e:
            return False, f"Error multipart: {e}"
    
    @classmethod
    def full_health_check(cls):
        """Health check completo"""
        results = {}
        
        # Test conectividad
        results['connectivity'] = cls.check_connectivity()
        
        # Test upload básico
        results['upload'] = cls.check_upload_capability()
        
        # Test multipart
        results['multipart'] = cls.check_multipart_capability()
        
        # Resumen
        all_ok = all(result[0] for result in results.values())
        
        return {
            'status': 'OK' if all_ok else 'ERROR',
            'details': results,
            'limits': get_r2_upload_limits(),
            'recommendations': optimize_r2_for_architecture_files() if all_ok else None
        }
