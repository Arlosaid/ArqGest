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
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando deployment de archivos estáticos...')
        )

        # Simular producción si es modo test
        if options['test']:
            self.stdout.write(
                self.style.WARNING('⚠️  Modo TEST: Para probar cache busting, usa: DEBUG=False python manage.py collectstatic')
            )
            self.stdout.write(
                self.style.WARNING('⚠️  El modo test requiere reiniciar Django con DEBUG=False')
            )
            return

        try:
            # Limpiar archivos estáticos anteriores si se fuerza
            if options['force']:
                self.stdout.write('🗑️  Limpiando archivos estáticos anteriores...')
                static_root = settings.STATIC_ROOT
                if os.path.exists(static_root):
                    import shutil
                    shutil.rmtree(static_root)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Directorio {static_root} limpiado')
                    )

            # Ejecutar collectstatic
            self.stdout.write('📦 Recopilando archivos estáticos...')
            call_command('collectstatic', '--noinput', verbosity=1)

            # Verificar que el manifest se generó correctamente
            manifest_path = os.path.join(settings.STATIC_ROOT, 'staticfiles.json')
            if os.path.exists(manifest_path):
                self.stdout.write(
                    self.style.SUCCESS('✅ Manifest de cache busting generado correctamente')
                )
                
                # Mostrar algunos ejemplos del manifest
                import json
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                self.stdout.write('\n📋 Ejemplos de archivos con cache busting:')
                count = 0
                for original, hashed in manifest.get('paths', {}).items():
                    if count < 5 and (original.endswith('.css') or original.endswith('.js')):
                        self.stdout.write(f'   {original} → {hashed}')
                        count += 1
                
                self.stdout.write(f'\n📊 Total de archivos con hash: {len(manifest.get("paths", {}))}\n')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ No se encontró el manifest de cache busting')
                )

            # Mostrar instrucciones
            self.stdout.write(self.style.SUCCESS('🎉 Deployment completado exitosamente!'))
            self.stdout.write('\n📝 Instrucciones para producción:')
            self.stdout.write('   1. Los archivos CSS/JS ahora tienen hash automático')
            self.stdout.write('   2. Los navegadores descargarán automáticamente nuevas versiones')
            self.stdout.write('   3. No necesitas pedir a usuarios que borren caché')
            self.stdout.write('   4. Los archivos se cachean por 1 año para máximo rendimiento\n')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante el deployment: {str(e)}')
            )
        finally:
            pass
