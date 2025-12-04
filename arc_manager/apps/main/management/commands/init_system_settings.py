# apps/main/management/commands/init_system_settings.py
from django.core.management.base import BaseCommand
from apps.main.models import SystemSettings


class Command(BaseCommand):
    help = 'Inicializa o actualiza la configuración del sistema con valores por defecto'

    def handle(self, *args, **options):
        settings = SystemSettings.load()
        
        self.stdout.write(self.style.SUCCESS('Configuración del sistema inicializada exitosamente'))
        self.stdout.write(f'  Modo mantenimiento: {"Activo" if settings.maintenance_mode else "Inactivo"}')
        self.stdout.write(f'  Empresa: {settings.company_name}')
        self.stdout.write(f'  Email soporte: {settings.support_email}')
        self.stdout.write(f'  Tamaño máximo de archivo: {settings.max_file_size_mb} MB')
        self.stdout.write(f'  Timeout de sesión: {settings.session_timeout_minutes} minutos')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Para modificar límites de usuarios y almacenamiento, edita los Planes directamente.'))
        self.stdout.write(self.style.WARNING('Visita: /admin/plans/plan/'))

