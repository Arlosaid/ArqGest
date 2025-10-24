"""
Management command para limpiar la caché de SystemSettings.
Útil cuando se actualiza la configuración en producción y no se refleja de inmediato.

Uso:
    python manage.py clear_settings_cache
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.main.models import SystemSettings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia la caché de SystemSettings y recarga la configuración'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔄 Limpiando caché de SystemSettings...'))
        
        # Limpiar caché
        cache.delete('system_settings')
        self.stdout.write(self.style.SUCCESS('✅ Caché limpiada'))
        
        # Recargar configuración
        settings = SystemSettings.load()
        
        self.stdout.write(self.style.SUCCESS('✅ Configuración recargada exitosamente'))
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('📊 Configuración actual:'))
        self.stdout.write(f'  • Tamaño máximo de archivo: {settings.max_file_size_mb} MB')
        self.stdout.write(f'  • Uploads por minuto: {settings.upload_requests_per_minute}')
        self.stdout.write(f'  • Uploads por hora: {settings.upload_requests_per_hour}')
        self.stdout.write(f'  • Tamaño total por hora: {settings.upload_size_per_hour_mb} MB')
        self.stdout.write(f'  • Almacenamiento Trial: {settings.storage_trial_gb} GB')
        self.stdout.write(f'  • Almacenamiento Básico: {settings.storage_basic_gb} GB')
        self.stdout.write(f'  • Última actualización: {settings.updated_at.strftime("%d/%m/%Y %H:%M:%S")}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Comando completado'))
