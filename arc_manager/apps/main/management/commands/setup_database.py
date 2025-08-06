from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
import os


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
            
            # Crear superusuario desde variables de entorno
            self.stdout.write("👤 Configurando superusuario...")
            User = get_user_model()
            
            ADMIN_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL')
            ADMIN_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            ADMIN_FIRST_NAME = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin')
            ADMIN_LAST_NAME = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User')

            if not User.objects.filter(email=ADMIN_EMAIL).exists():
                if ADMIN_EMAIL and ADMIN_PASSWORD:
                    User.objects.create_superuser(
                        email=ADMIN_EMAIL,
                        password=ADMIN_PASSWORD,
                        first_name=ADMIN_FIRST_NAME,
                        last_name=ADMIN_LAST_NAME
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ Superusuario '{ADMIN_EMAIL}' creado."))
                else:
                    self.stdout.write(self.style.WARNING("⚠️ No se creará superusuario. Faltan las variables de entorno DJANGO_SUPERUSER_EMAIL o DJANGO_SUPERUSER_PASSWORD."))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Superusuario '{ADMIN_EMAIL}' ya existe."))
            
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