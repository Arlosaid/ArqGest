# core/management/commands/test_r2.py
"""
Comando para probar la configuración de R2 con archivos grandes
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Probar configuración de R2 para archivos grandes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-size',
            type=str,
            default='100MB',
            help='Tamaño del archivo de test (ej: 100MB, 500MB, 1GB)'
        )
        parser.add_argument(
            '--skip-large',
            action='store_true',
            help='Saltar test de archivos grandes'
        )
        
    def handle(self, *args, **options):
        self.stdout.write("🧪 Iniciando tests de configuración R2...")
        
        # Verificar configuración
        if not self._check_r2_config():
            return
        
        # Health check básico
        if not self._basic_health_check():
            return
            
        # Test de archivos grandes (opcional)
        if not options['skip_large']:
            self._test_large_file_upload(options['test_size'])
        
        self.stdout.write(self.style.SUCCESS("✅ Tests R2 completados"))
    
    def _check_r2_config(self):
        """Verificar configuración básica"""
        self.stdout.write("📋 Verificando configuración R2...")
        
        required_settings = [
            'AWS_S3_ENDPOINT_URL',
            'AWS_STORAGE_BUCKET_NAME', 
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY'
        ]
        
        missing = []
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing.append(setting)
        
        if missing:
            self.stdout.write(
                self.style.ERROR(f"❌ Configuración faltante: {', '.join(missing)}")
            )
            return False
        
        # Verificar que ENABLE_STORAGES esté activado
        if os.environ.get('ENABLE_STORAGES', 'false').lower() != 'true':
            self.stdout.write(
                self.style.ERROR("❌ ENABLE_STORAGES no está activado")
            )
            return False
        
        self.stdout.write(self.style.SUCCESS("✅ Configuración básica OK"))
        return True
    
    def _basic_health_check(self):
        """Health check básico"""
        self.stdout.write("🔍 Ejecutando health check...")
        
        try:
            from core.r2_config import R2HealthCheck
            
            # Health check completo
            result = R2HealthCheck.full_health_check()
            
            if result['status'] == 'OK':
                self.stdout.write(self.style.SUCCESS("✅ Health check OK"))
                
                # Mostrar límites
                limits = result['limits']
                self.stdout.write("📊 Límites actuales:")
                for key, value in limits.items():
                    self.stdout.write(f"  • {key}: {value}")
                
                return True
            else:
                self.stdout.write(self.style.ERROR("❌ Health check falló"))
                for test, (success, message) in result['details'].items():
                    status = "✅" if success else "❌"
                    self.stdout.write(f"  {status} {test}: {message}")
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en health check: {e}")
            )
            return False
    
    def _test_large_file_upload(self, size_str):
        """Test de upload de archivo grande"""
        self.stdout.write(f"📤 Testing upload de archivo {size_str}...")
        
        # Parsear tamaño
        size_bytes = self._parse_size(size_str)
        if size_bytes > 2 * 1024 * 1024 * 1024:  # 2GB
            self.stdout.write(
                self.style.WARNING("⚠️  Test de archivo muy grande (>2GB) saltado")
            )
            return
        
        try:
            from core.r2_config import get_optimized_r2_client
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                self.stdout.write(f"📝 Creando archivo temporal de {size_str}...")
                
                # Escribir datos de test
                chunk_size = 1024 * 1024  # 1MB chunks
                written = 0
                
                while written < size_bytes:
                    chunk = b'0' * min(chunk_size, size_bytes - written)
                    temp_file.write(chunk)
                    written += len(chunk)
                    
                    # Progress
                    if written % (10 * 1024 * 1024) == 0:  # Cada 10MB
                        progress = (written / size_bytes) * 100
                        self.stdout.write(f"  📝 Progreso: {progress:.1f}%")
                
                temp_file_path = temp_file.name
            
            # Upload a R2
            self.stdout.write("📤 Subiendo a R2...")
            client = get_optimized_r2_client()
            
            test_key = f'test-uploads/large-file-test-{size_str}.bin'
            
            with open(temp_file_path, 'rb') as f:
                client.upload_fileobj(
                    f,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    test_key
                )
            
            # Verificar upload
            response = client.head_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key
            )
            
            uploaded_size = response['ContentLength']
            
            if uploaded_size == size_bytes:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Upload exitoso: {uploaded_size} bytes")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Tamaño incorrecto: esperado {size_bytes}, obtenido {uploaded_size}"
                    )
                )
            
            # Limpiar
            client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key
            )
            os.unlink(temp_file_path)
            
            self.stdout.write("🧹 Archivos temporales limpiados")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en test de archivo grande: {e}")
            )
    
    def _parse_size(self, size_str):
        """Parsear string de tamaño a bytes"""
        size_str = size_str.upper().strip()
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                number = float(size_str[:-len(suffix)])
                return int(number * multiplier)
        
        # Si no tiene sufijo, asumir bytes
        return int(size_str)
