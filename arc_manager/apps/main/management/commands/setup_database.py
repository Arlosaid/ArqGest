from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Configura la base de datos automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la ejecución incluso si hay errores',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write("🔄 Iniciando configuración de base de datos...")
        
        # Verificar conexión a la base de datos
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('✅ Conexión a base de datos exitosa'))
        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error de conexión a base de datos: {e}')
            )
            if not force:
                return
        
        try:
            # Ejecutar migraciones
            self.stdout.write("🔄 Ejecutando migraciones...")
            call_command('migrate', verbosity=2, interactive=False)
            self.stdout.write(self.style.SUCCESS("✅ Migraciones completadas"))
            
            # Configurar planes
            self.stdout.write("📋 Configurando planes...")
            try:
                call_command('setup_mvp_plans')
                self.stdout.write(self.style.SUCCESS("✅ Planes configurados"))
            except Exception as e:
                if force:
                    self.stdout.write(self.style.WARNING(f"⚠️ Error en planes: {e}"))
                else:
                    raise
            
            self.stdout.write(self.style.SUCCESS("🎉 ¡Configuración de base de datos completada exitosamente!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error durante la configuración: {e}"))
            if force:
                self.stdout.write(self.style.WARNING("⚠️ Continuando debido a --force"))
            else:
                raise 