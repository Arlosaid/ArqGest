# apps/main/management/commands/init_system_settings.py
from django.core.management.base import BaseCommand
from apps.main.models import SystemSettings


class Command(BaseCommand):
    help = 'Inicializa o actualiza la configuración del sistema con valores por defecto'

    def handle(self, *args, **options):
        settings = SystemSettings.load()
        
        self.stdout.write(self.style.SUCCESS('Configuración del sistema inicializada exitosamente'))
        self.stdout.write(f'  Usuarios máximos (Trial): {settings.max_users_trial}')
        self.stdout.write(f'  Usuarios máximos (Básico): {settings.max_users_basic}')
        self.stdout.write(f'  Almacenamiento (Trial): {settings.storage_trial_gb} GB')
        self.stdout.write(f'  Almacenamiento (Básico): {settings.storage_basic_gb} GB')
        self.stdout.write(f'  Tamaño máximo de archivo: {settings.max_file_size_mb} MB')
        self.stdout.write(f'  Timeout de sesión: {settings.session_timeout_minutes} minutos')
        self.stdout.write(f'  Duración del trial: {settings.trial_duration_days} días')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Puedes modificar estas configuraciones desde el panel de administración de Django'))
        self.stdout.write(self.style.WARNING('Visita: /admin/main/systemsettings/'))

