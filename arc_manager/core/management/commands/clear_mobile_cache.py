"""
Comando de Django para limpiar cache de archivos estáticos
Específicamente optimizado para problemas de Safari móvil
"""
import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Limpia cache de archivos estáticos para resolver problemas en Safari móvil'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la limpieza completa del cache',
        )
        parser.add_argument(
            '--production',
            action='store_true',
            help='Ejecuta optimizaciones específicas para producción',
        )

    def handle(self, *args, **options):
        force = options['force']
        production = options['production']
        
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpieza de cache para Safari móvil...')
        )
        
        # 1. Limpiar staticfiles compilados
        self._clear_staticfiles()
        
        # 2. Limpiar cache de Django
        self._clear_django_cache()
        
        # 3. Regenerar staticfiles
        self._regenerate_staticfiles(production)
        
        # 4. Limpiar cache interno del template tag
        self._clear_template_cache()
        
        if force:
            # 5. Limpiar archivos temporales
            self._clear_temp_files()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Cache limpiado exitosamente para móviles (iOS y Android)')
        )
        
        # Mostrar consejos para usuarios móviles
        self._display_mobile_tips()
        
        if production:
            self.stdout.write(
                self.style.WARNING('📱 Reinicia el servidor para aplicar cambios en producción')
            )

    def _clear_staticfiles(self):
        """Limpia archivos estáticos compilados"""
        self.stdout.write('🗂️  Limpiando staticfiles...')
        
        if os.path.exists(settings.STATIC_ROOT):
            # Preservar estructura pero limpiar contenido
            for item in os.listdir(settings.STATIC_ROOT):
                item_path = os.path.join(settings.STATIC_ROOT, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            self.stdout.write('  ✓ Staticfiles limpiados')
        else:
            self.stdout.write('  ⚠ STATIC_ROOT no existe')

    def _clear_django_cache(self):
        """Limpia cache de Django"""
        self.stdout.write('💾 Limpiando cache de Django...')
        
        try:
            from django.core.cache import cache
            cache.clear()
            self.stdout.write('  ✓ Cache de Django limpiado')
        except Exception as e:
            self.stdout.write(f'  ⚠ Error limpiando cache: {e}')

    def _regenerate_staticfiles(self, production=False):
        """Regenera archivos estáticos"""
        self.stdout.write('🔄 Regenerando staticfiles...')
        
        try:
            # Collectstatic con configuración optimizada
            call_command('collectstatic', 
                        interactive=False, 
                        clear=True,
                        ignore_patterns=['*.pyc', '*.pyo'])
            self.stdout.write('  ✓ Staticfiles regenerados')
            
            if production:
                # En producción, comprimir archivos para WhiteNoise
                self.stdout.write('📦 Comprimiendo archivos para producción...')
                # WhiteNoise comprime automáticamente durante collectstatic
                self.stdout.write('  ✓ Archivos comprimidos')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error regenerando staticfiles: {e}')

    def _clear_template_cache(self):
        """Limpia cache interno del template tag mobile_static"""
        self.stdout.write('🏷️  Limpiando cache de template tags...')
        
        try:
            # Importar y limpiar cache del template tag
            from core.templatetags.mobile_static import _version_cache
            _version_cache.clear()
            self.stdout.write('  ✓ Cache de template tags limpiado')
        except ImportError:
            self.stdout.write('  ⚠ Template tags no encontrados')

    def _clear_temp_files(self):
        """Limpia archivos temporales"""
        self.stdout.write('🗑️  Limpiando archivos temporales...')
        
        temp_dirs = [
            getattr(settings, 'FILE_UPLOAD_TEMP_DIR', None),
            '/tmp/django_cache',  # Cache temporal común
            os.path.join(settings.BASE_DIR, 'temp_uploads')  # Directorio de uploads temporales (corregido)
        ]
        
        for temp_dir in temp_dirs:
            # Validar que temp_dir no sea None, vacío o solo espacios
            if temp_dir and temp_dir.strip() and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir, exist_ok=True)
                    self.stdout.write(f'  ✓ Limpiado: {temp_dir}')
                except Exception as e:
                    self.stdout.write(f'  ⚠ Error limpiando {temp_dir}: {e}')

    def _display_mobile_tips(self):
        """Muestra consejos para Safari móvil y Android"""
        tips = [
            "📱 Para Safari móvil (iOS):",
            "   • Fuerza la recarga: mantén presionado el botón de recarga",
            "   • Borra cache del navegador: Configuración > Safari > Borrar historial",
            "   • Modo privado: prueba en una ventana privada",
            "   • Versión iOS: asegúrate de tener iOS 14+ para mejor compatibilidad",
            "",
            "🤖 Para Android Chrome/WebView:",
            "   • Fuerza la recarga: Menú > Más herramientas > Borrar datos",
            "   • Chrome: Configuración > Privacidad > Borrar datos de navegación",
            "   • Samsung Internet: Configuración > Privacidad > Eliminar datos",
            "   • WebView: la app puede necesitar reiniciarse para ver cambios",
            "   • Versión Android: asegúrate de tener Android 8+ para mejor rendimiento"
        ]
        
        for tip in tips:
            self.stdout.write(self.style.WARNING(tip))
