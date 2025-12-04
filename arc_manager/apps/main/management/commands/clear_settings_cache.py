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
        self.stdout.write(self.style.WARNING('🔄 Limpiando TODOS los cachés relacionados...'))
        
        # Limpiar caché de SystemSettings
        cache.delete('system_settings')
        cache.delete('filelimitssettings_settings')
        self.stdout.write(self.style.SUCCESS('  ✅ Caché de SystemSettings limpiado'))
        
        # Limpiar cachés de planes
        cache.delete('plans_cache')
        cache.delete('active_plans_cache')
        self.stdout.write(self.style.SUCCESS('  ✅ Caché de Planes limpiado'))
        
        # Limpiar cachés de organizaciones
        from apps.orgs.models import Organization
        org_count = 0
        for org in Organization.objects.all():
            org.invalidate_user_cache()
            org.invalidate_storage_cache()
            org_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✅ Caché de {org_count} organizaciones limpiado'))
        
        # Recargar configuración
        settings = SystemSettings.load()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📊 Configuración actual del sistema:'))
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('  📄 ARCHIVOS:'))
        self.stdout.write(f'    • Tamaño máximo: {settings.max_file_size_mb} MB')
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('  🚦 RATE LIMITING:'))
        self.stdout.write(f'    • Uploads/minuto: {settings.upload_requests_per_minute}')
        self.stdout.write(f'    • Uploads/hora: {settings.upload_requests_per_hour}')
        self.stdout.write(f'    • MB/hora: {settings.upload_size_per_hour_mb}')
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('  🔧 MANTENIMIENTO:'))
        self.stdout.write(f'    • Modo: {"ACTIVO" if settings.maintenance_mode else "Inactivo"}')
        self.stdout.write('')
        self.stdout.write(f'  📅 Última actualización: {settings.updated_at.strftime("%d/%m/%Y %H:%M:%S")}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Todos los cachés limpiados. Los cambios se aplicarán inmediatamente.'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('NOTA: Para límites de usuarios/almacenamiento, edita los Planes directamente en /admin/plans/plan/'))
