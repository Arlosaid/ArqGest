import os
import shutil
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage


class Command(BaseCommand):
    help = 'Diagnostica y soluciona problemas con archivos estáticos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar archivos estáticos antes de recolectar',
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Solo verificar configuración sin hacer cambios',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 Diagnosticando archivos estáticos...")
        
        # Verificar configuración
        self.verify_static_config()
        
        if options['verify']:
            return
        
        # Limpiar si se solicita
        if options['clear']:
            self.clear_static_files()
        
        # Recolectar archivos estáticos
        self.collect_static_files()
        
        # Verificar archivos críticos
        self.verify_critical_files()
        
        self.stdout.write(
            self.style.SUCCESS("✅ Archivos estáticos procesados correctamente")
        )
    
    def verify_static_config(self):
        """Verificar configuración de archivos estáticos"""
        self.stdout.write("📋 Verificando configuración...")
        
        # Verificar STATIC_URL
        self.stdout.write(f"STATIC_URL: {settings.STATIC_URL}")
        
        # Verificar STATIC_ROOT
        self.stdout.write(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        if not os.path.exists(settings.STATIC_ROOT):
            os.makedirs(settings.STATIC_ROOT, exist_ok=True)
            self.stdout.write("📁 Directorio STATIC_ROOT creado")
        
        # Verificar STATICFILES_DIRS
        self.stdout.write(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        for static_dir in settings.STATICFILES_DIRS:
            if not os.path.exists(static_dir):
                self.stdout.write(
                    self.style.WARNING(f"⚠️ Directorio no existe: {static_dir}")
                )
        
        # Verificar STATICFILES_STORAGE
        self.stdout.write(f"STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
        
        # Verificar WhiteNoise
        if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
            self.stdout.write("✅ WhiteNoise middleware configurado")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ WhiteNoise middleware no encontrado")
            )
    
    def clear_static_files(self):
        """Limpiar archivos estáticos existentes"""
        self.stdout.write("🧹 Limpiando archivos estáticos...")
        
        if os.path.exists(settings.STATIC_ROOT):
            shutil.rmtree(settings.STATIC_ROOT)
            self.stdout.write("📁 Directorio STATIC_ROOT limpiado")
        
        os.makedirs(settings.STATIC_ROOT, exist_ok=True)
    
    def collect_static_files(self):
        """Recolectar archivos estáticos"""
        self.stdout.write("📦 Recolectando archivos estáticos...")
        
        try:
            call_command('collectstatic', verbosity=1, interactive=False, clear=True)
            self.stdout.write("✅ Archivos estáticos recolectados")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error al recolectar archivos estáticos: {e}")
            )
            
            # Intentar con configuración alternativa
            self.stdout.write("🔄 Intentando con configuración alternativa...")
            try:
                # Cambiar temporalmente el storage
                original_storage = settings.STATICFILES_STORAGE
                settings.STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
                
                call_command('collectstatic', verbosity=1, interactive=False, clear=True)
                self.stdout.write("✅ Archivos estáticos recolectados con configuración alternativa")
                
                # Restaurar configuración
                settings.STATICFILES_STORAGE = original_storage
                
            except Exception as e2:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error con configuración alternativa: {e2}")
                )
    
    def verify_critical_files(self):
        """Verificar que archivos críticos estén disponibles"""
        self.stdout.write("🔍 Verificando archivos críticos...")
        
        critical_files = [
            'css/base.css',
            'css/auth.css',
            'css/dashboard.css',
            'js/base.js',
            'images/logo.png',
        ]
        
        for file_path in critical_files:
            # Buscar archivo en directorios de desarrollo
            found = finders.find(file_path)
            if found:
                self.stdout.write(f"✅ Encontrado en desarrollo: {file_path}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ No encontrado en desarrollo: {file_path}")
                )
            
            # Verificar en archivos estáticos recolectados
            static_path = os.path.join(settings.STATIC_ROOT, file_path)
            if os.path.exists(static_path):
                self.stdout.write(f"✅ Disponible en producción: {file_path}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ No disponible en producción: {file_path}")
                )
