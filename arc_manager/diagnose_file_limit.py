#!/usr/bin/env python
"""
Script de diagnóstico para verificar el límite de tamaño de archivo
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.main.models import SystemSettings
from django.core.cache import cache

print("=" * 60)
print("DIAGNÓSTICO DE LÍMITE DE TAMAÑO DE ARCHIVO")
print("=" * 60)

# 1. Verificar valor en base de datos
try:
    settings = SystemSettings.objects.get(pk=1)
    print(f"\n✅ SystemSettings encontrado en BD:")
    print(f"   - max_file_size_mb: {settings.max_file_size_mb}")
    if hasattr(settings, 'max_upload_size_per_request_mb'):
        print(f"   - max_upload_size_per_request_mb: {settings.max_upload_size_per_request_mb}")
    if hasattr(settings, 'max_projects_per_org'):
        print(f"   - max_projects_per_org: {settings.max_projects_per_org}")
except SystemSettings.DoesNotExist:
    print("\n❌ ERROR: SystemSettings no existe en BD")
    print("   Ejecuta: python manage.py shell -c \"from apps.main.models import SystemSettings; SystemSettings.objects.create()\"")

# 2. Verificar método load()
try:
    loaded_settings = SystemSettings.load()
    print(f"\n✅ SystemSettings.load() funciona:")
    print(f"   - max_file_size_mb: {loaded_settings.max_file_size_mb}")
except Exception as e:
    print(f"\n❌ ERROR en SystemSettings.load(): {e}")

# 3. Verificar caché
cache_key = 'systemsettings_settings'
cached = cache.get(cache_key)
if cached:
    print(f"\n⚠️  Valor en CACHÉ encontrado:")
    print(f"   - max_file_size_mb: {cached.max_file_size_mb}")
    print(f"   - Limpiando caché...")
    cache.delete(cache_key)
    print(f"   ✅ Caché limpiado")
else:
    print(f"\n✅ No hay valor en caché (correcto)")

# 4. Verificar context processor
from core.context_processors import global_settings
from django.test import RequestFactory

factory = RequestFactory()
request = factory.get('/')
context = global_settings(request)
print(f"\n✅ Context processor global_settings():")
print(f"   - max_file_size_mb: {context.get('max_file_size_mb', 'NO ENCONTRADO')}")

# 5. Verificar variable de entorno
env_max_size = os.environ.get('MAX_FILE_SIZE_MB', 'NO DEFINIDO')
print(f"\n📋 Variable de entorno MAX_FILE_SIZE_MB: {env_max_size}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 60)
print("\n💡 RECOMENDACIONES:")
print("   1. Si max_file_size_mb en BD no es 1500, actualízalo desde /admin/")
print("   2. Si había caché, ya fue limpiado - recarga la página")
print("   3. Verifica que el template use {{ max_file_size_mb }}")
print("   4. Reinicia el servidor: docker-compose restart web")
print()
