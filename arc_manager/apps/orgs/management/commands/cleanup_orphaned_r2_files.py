"""
Comando para limpiar archivos huérfanos en R2/S3
Útil para limpiar carpetas de organizaciones eliminadas
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.orgs.models import Organization
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia archivos huérfanos de organizaciones eliminadas en R2/S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se eliminaría sin hacerlo realmente',
        )
        parser.add_argument(
            '--org-id',
            type=int,
            help='ID específico de organización para limpiar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_org_id = options.get('org_id')
        
        self.stdout.write(self.style.WARNING('🔍 Limpieza de archivos huérfanos en R2/S3'))
        
        # Verificar si R2 está habilitado
        if os.environ.get('ENABLE_STORAGES', 'false').lower() != 'true':
            self.stdout.write(self.style.ERROR('❌ R2/S3 no está habilitado (ENABLE_STORAGES=false)'))
            return
        
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            self.stdout.write(self.style.ERROR('❌ boto3 no está instalado'))
            return
        
        try:
            # Obtener cliente R2
            from core.r2_config import get_optimized_r2_client
            s3_client = get_optimized_r2_client()
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            
            self.stdout.write(f'📦 Bucket: {bucket_name}')
            
            # Obtener IDs de organizaciones existentes
            existing_org_ids = set(Organization.objects.values_list('id', flat=True))
            self.stdout.write(f'✅ {len(existing_org_ids)} organizaciones activas en DB')
            
            # Listar carpetas en R2
            self.stdout.write('\n🔍 Escaneando carpetas en R2...')
            
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=bucket_name,
                Prefix='organizations/',
                Delimiter='/'
            )
            
            orphaned_folders = []
            total_size = 0
            
            for page in pages:
                # Obtener las "carpetas" (CommonPrefixes)
                if 'CommonPrefixes' in page:
                    for prefix in page['CommonPrefixes']:
                        folder_path = prefix['Prefix']
                        
                        # Extraer ID de organización de la ruta
                        # Formato: organizations/123/
                        try:
                            parts = folder_path.strip('/').split('/')
                            if len(parts) >= 2 and parts[0] == 'organizations':
                                org_id = int(parts[1])
                                
                                # Si se especificó un org_id, solo procesar ese
                                if specific_org_id and org_id != specific_org_id:
                                    continue
                                
                                # Verificar si la organización existe
                                if org_id not in existing_org_ids:
                                    orphaned_folders.append((org_id, folder_path))
                                    self.stdout.write(
                                        self.style.WARNING(f'   🗑️  Organización {org_id} (eliminada) - {folder_path}')
                                    )
                        except (ValueError, IndexError):
                            # No es un ID válido, ignorar
                            continue
            
            if not orphaned_folders:
                self.stdout.write(self.style.SUCCESS('\n✅ No se encontraron carpetas huérfanas'))
                return
            
            self.stdout.write(f'\n📊 Encontradas {len(orphaned_folders)} carpetas huérfanas')
            
            # Procesar cada carpeta huérfana
            total_files_deleted = 0
            
            for org_id, folder_path in orphaned_folders:
                self.stdout.write(f'\n📂 Procesando: {folder_path}')
                
                # Listar archivos en esta carpeta
                file_pages = paginator.paginate(Bucket=bucket_name, Prefix=folder_path)
                
                files_to_delete = []
                folder_size = 0
                
                for file_page in file_pages:
                    if 'Contents' not in file_page:
                        continue
                    
                    for obj in file_page['Contents']:
                        file_key = obj['Key']
                        file_size = obj.get('Size', 0)
                        
                        files_to_delete.append({'Key': file_key})
                        folder_size += file_size
                        
                        # Eliminar en lotes de 1000
                        if len(files_to_delete) >= 1000:
                            if not dry_run:
                                response = s3_client.delete_objects(
                                    Bucket=bucket_name,
                                    Delete={'Objects': files_to_delete}
                                )
                                deleted_count = len(response.get('Deleted', []))
                                total_files_deleted += deleted_count
                                
                                if 'Errors' in response:
                                    for error in response['Errors']:
                                        self.stdout.write(
                                            self.style.ERROR(f"      ❌ Error: {error['Key']} - {error['Message']}")
                                        )
                            else:
                                total_files_deleted += len(files_to_delete)
                            
                            self.stdout.write(f'      🗑️  {len(files_to_delete)} archivos marcados')
                            files_to_delete = []
                
                # Eliminar archivos restantes
                if files_to_delete:
                    if not dry_run:
                        response = s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': files_to_delete}
                        )
                        deleted_count = len(response.get('Deleted', []))
                        total_files_deleted += deleted_count
                        
                        if 'Errors' in response:
                            for error in response['Errors']:
                                self.stdout.write(
                                    self.style.ERROR(f"      ❌ Error: {error['Key']} - {error['Message']}")
                                )
                    else:
                        total_files_deleted += len(files_to_delete)
                    
                    self.stdout.write(f'      🗑️  {len(files_to_delete)} archivos marcados')
                
                folder_size_mb = folder_size / (1024 * 1024)
                total_size += folder_size
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Carpeta procesada: {folder_size_mb:.2f} MB')
                )
            
            # Resumen final
            total_size_mb = total_size / (1024 * 1024)
            total_size_gb = total_size_mb / 1024
            
            self.stdout.write('\n' + '='*60)
            
            if dry_run:
                self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN (no se eliminó nada)'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ LIMPIEZA COMPLETADA'))
            
            self.stdout.write(f'📊 Carpetas huérfanas: {len(orphaned_folders)}')
            self.stdout.write(f'📄 Archivos {"encontrados" if dry_run else "eliminados"}: {total_files_deleted}')
            self.stdout.write(f'💾 Espacio {"recuperable" if dry_run else "liberado"}: {total_size_gb:.2f} GB ({total_size_mb:.2f} MB)')
            
            if dry_run:
                self.stdout.write('\n💡 Ejecuta sin --dry-run para eliminar realmente los archivos')
            
            self.stdout.write('='*60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}'))
            logger.exception('Error en cleanup_orphaned_r2_files')
