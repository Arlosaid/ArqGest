"""
Comando personalizado para deployment de archivos estáticos con cache busting.
Facilita el proceso de actualización en producción.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Despliega archivos estáticos con cache busting para producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la regeneración de todos los archivos estáticos',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Modo test: simula producción para probar cache busting',
        )

    def handle(self, *args, **options):
        # Simular producción si es modo test
        if options['test']:
            self.stdout.write(
                'Modo TEST: Usa DEBUG=False para probar cache busting'
            )
            return

        try:
            # Limpiar archivos estáticos anteriores si se fuerza
            if options['force']:
                static_root = settings.STATIC_ROOT
                if os.path.exists(static_root):
                    import shutil
                    shutil.rmtree(static_root)

            # Ejecutar collectstatic
            call_command('collectstatic', '--noinput', verbosity=0)

            # Verificar que el manifest se generó correctamente
            manifest_path = os.path.join(settings.STATIC_ROOT, 'staticfiles.json')
            if os.path.exists(manifest_path):
                self.stdout.write('Static files deployed successfully')
            else:
                self.stdout.write(self.style.ERROR('Error: manifest not found'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
