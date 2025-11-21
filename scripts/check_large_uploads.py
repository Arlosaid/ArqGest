#!/usr/bin/env python
"""
Script para diagnosticar problemas con uploads de archivos grandes.
Uso: docker-compose exec web python scripts/check_large_uploads.py [phase_id]
"""

import os
import sys
import django

# Agregar el directorio arc_manager al path
sys.path.insert(0, '/app/arc_manager')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.files.models import ProjectFile
from apps.projects.models import Phase
from django.contrib.auth import get_user_model

User = get_user_model()

def check_recent_uploads():
    """Verificar uploads recientes"""
    print("\n" + "="*80)
    print("VERIFICACIÓN DE UPLOADS RECIENTES")
    print("="*80)
    
    # Últimos 20 archivos subidos
    recent_files = ProjectFile.objects.select_related(
        'phase', 'uploaded_by'
    ).order_by('-uploaded_at')[:20]
    
    if not recent_files:
        print("\n❌ No se encontraron archivos en la base de datos")
        return
    
    print(f"\n✅ Últimos 20 archivos subidos:\n")
    for f in recent_files:
        size_mb = f.file.size / (1024 * 1024) if f.file else 0
        exists = "✅" if f.file and os.path.exists(f.file.path) else "❌"
        
        print(f"{exists} ID: {f.id:5d} | Fase: {f.phase_id:3d} | "
              f"{size_mb:8.2f} MB | {f.filename[:50]:<50s} | "
              f"{f.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}")


def check_large_files(min_size_mb=100):
    """Verificar archivos grandes (>100 MB)"""
    print("\n" + "="*80)
    print(f"ARCHIVOS GRANDES (> {min_size_mb} MB)")
    print("="*80)
    
    large_files = ProjectFile.objects.select_related(
        'phase', 'uploaded_by'
    ).order_by('-uploaded_at')
    
    found = False
    for f in large_files:
        try:
            size_mb = f.file.size / (1024 * 1024) if f.file else 0
            if size_mb >= min_size_mb:
                found = True
                exists = os.path.exists(f.file.path) if f.file else False
                status = "✅ Existe" if exists else "❌ NO existe en disco"
                
                print(f"\n{status}")
                print(f"  ID: {f.id}")
                print(f"  Archivo: {f.filename}")
                print(f"  Tamaño: {size_mb:.2f} MB")
                print(f"  Fase: {f.phase_id} - {f.phase.name}")
                print(f"  Subido: {f.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Usuario: {f.uploaded_by.email if f.uploaded_by else 'N/A'}")
                print(f"  Path: {f.file.name if f.file else 'N/A'}")
                
                if exists:
                    actual_size = os.path.getsize(f.file.path) / (1024 * 1024)
                    print(f"  Tamaño en disco: {actual_size:.2f} MB")
                    if abs(actual_size - size_mb) > 0.1:
                        print(f"  ⚠️  ADVERTENCIA: Tamaño en disco no coincide con DB")
        except Exception as e:
            print(f"\n❌ Error al verificar archivo ID {f.id}: {e}")
    
    if not found:
        print(f"\n❌ No se encontraron archivos > {min_size_mb} MB")


def check_phase_files(phase_id):
    """Verificar archivos de una fase específica"""
    print("\n" + "="*80)
    print(f"ARCHIVOS EN FASE {phase_id}")
    print("="*80)
    
    try:
        phase = Phase.objects.get(id=phase_id)
        print(f"\nFase: {phase.name}")
        print(f"Proyecto: {phase.project.name}")
    except Phase.DoesNotExist:
        print(f"\n❌ Fase {phase_id} no existe")
        return
    
    files = ProjectFile.objects.filter(phase_id=phase_id).order_by('-uploaded_at')
    
    if not files:
        print(f"\n❌ No hay archivos en esta fase")
        return
    
    print(f"\n✅ {files.count()} archivo(s) encontrado(s):\n")
    
    total_size = 0
    for f in files:
        size_mb = f.file.size / (1024 * 1024) if f.file else 0
        total_size += size_mb
        exists = "✅" if f.file and os.path.exists(f.file.path) else "❌"
        
        print(f"{exists} {f.filename} - {size_mb:.2f} MB - {f.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\nTamaño total: {total_size:.2f} MB")


def check_duplicates():
    """Verificar archivos duplicados por checksum"""
    print("\n" + "="*80)
    print("VERIFICACIÓN DE DUPLICADOS")
    print("="*80)
    
    from django.db.models import Count
    
    duplicates = ProjectFile.objects.filter(
        checksum_sha256__isnull=False
    ).values('checksum_sha256').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if not duplicates:
        print("\n✅ No se encontraron duplicados")
        return
    
    print(f"\n⚠️  Se encontraron {duplicates.count()} checksums duplicados:\n")
    
    for dup in duplicates:
        checksum = dup['checksum_sha256']
        count = dup['count']
        files = ProjectFile.objects.filter(checksum_sha256=checksum)
        
        print(f"\nChecksum: {checksum[:16]}... ({count} archivos)")
        for f in files:
            size_mb = f.file.size / (1024 * 1024) if f.file else 0
            print(f"  - ID: {f.id} | {f.filename} | {size_mb:.2f} MB | Fase: {f.phase_id}")


def check_storage_settings():
    """Verificar configuración de storage"""
    print("\n" + "="*80)
    print("CONFIGURACIÓN DE STORAGE")
    print("="*80)
    
    from apps.main.models import SystemSettings
    from django.conf import settings
    
    sys_settings = SystemSettings.load()
    
    print(f"\nTamaño máximo de archivo: {sys_settings.max_file_size_mb} MB")
    print(f"Tamaño máximo para checksum: {sys_settings.max_checksum_size_mb} MB")
    print(f"Memoria máxima para uploads: {sys_settings.data_upload_max_memory_mb} MB")
    
    print(f"\nDjango Settings:")
    print(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"  FILE_UPLOAD_TEMP_DIR: {settings.FILE_UPLOAD_TEMP_DIR}")
    print(f"  DATA_UPLOAD_MAX_MEMORY_SIZE: {settings.DATA_UPLOAD_MAX_MEMORY_SIZE / (1024*1024):.2f} MB")
    print(f"  DATA_UPLOAD_MAX_NUMBER_SIZE: {settings.DATA_UPLOAD_MAX_NUMBER_SIZE / (1024*1024):.2f} MB")
    
    # Verificar espacio en disco
    import shutil
    if os.path.exists(settings.MEDIA_ROOT):
        stat = shutil.disk_usage(settings.MEDIA_ROOT)
        print(f"\nEspacio en disco (MEDIA_ROOT):")
        print(f"  Total: {stat.total / (1024**3):.2f} GB")
        print(f"  Usado: {stat.used / (1024**3):.2f} GB")
        print(f"  Libre: {stat.free / (1024**3):.2f} GB")
        print(f"  Porcentaje usado: {(stat.used / stat.total * 100):.1f}%")


if __name__ == '__main__':
    import sys
    
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE UPLOADS DE ARCHIVOS GRANDES")
    print("="*80)
    
    # Verificaciones automáticas
    check_storage_settings()
    check_recent_uploads()
    check_large_files(min_size_mb=100)
    check_duplicates()
    
    # Si se especifica un phase_id como argumento
    if len(sys.argv) > 1:
        try:
            phase_id = int(sys.argv[1])
            check_phase_files(phase_id)
        except ValueError:
            print(f"\n❌ Error: '{sys.argv[1]}' no es un ID de fase válido")
    
    print("\n" + "="*80)
    print("Para verificar una fase específica:")
    print("  docker-compose exec web python scripts/check_large_uploads.py <phase_id>")
    print("="*80 + "\n")

