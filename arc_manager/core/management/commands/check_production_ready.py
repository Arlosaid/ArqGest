# core/management/commands/check_production_ready.py
"""
Comando para verificar si el sistema está listo para producción
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys


class Command(BaseCommand):
    help = 'Verificar si el sistema está listo para producción'
    
    def handle(self, *args, **options):
        self.stdout.write("Verificando configuración de producción...\n")
        
        issues = []
        warnings = []
        success = []
        
        # 1. Verificar DEBUG
        if settings.DEBUG:
            issues.append("ERROR: DEBUG=True - Debe estar en False para producción")
        else:
            success.append("OK: DEBUG=False")
        
        # 2. Verificar SECRET_KEY
        secret_key = settings.SECRET_KEY
        if not secret_key or secret_key == 'dev-insecure-key' or 'dev' in secret_key.lower() or 'change' in secret_key.lower():
            issues.append("ERROR: SECRET_KEY no es segura - Genera una nueva para producción")
        elif len(secret_key) < 50:
            warnings.append("WARNING: SECRET_KEY es corta - Recomendado >50 caracteres")
        else:
            success.append("OK: SECRET_KEY parece segura")
        
        # 3. Verificar ALLOWED_HOSTS
        allowed_hosts = settings.ALLOWED_HOSTS
        if '*' in allowed_hosts:
            issues.append("ERROR: ALLOWED_HOSTS='*' - Especifica dominios exactos")
        elif 'localhost' in allowed_hosts or '127.0.0.1' in allowed_hosts:
            warnings.append("WARNING: ALLOWED_HOSTS incluye localhost - Remover en producción")
        elif not allowed_hosts:
            issues.append("ERROR: ALLOWED_HOSTS vacío - Configura tus dominios")
        else:
            success.append(f"OK: ALLOWED_HOSTS configurado: {', '.join(allowed_hosts[:3])}")
        
        # 4. Verificar Storage R2
        enable_storages = os.environ.get('ENABLE_STORAGES', 'false').lower()
        if enable_storages != 'true':
            warnings.append("WARNING: ENABLE_STORAGES=false - Recomendado usar R2 en producción")
        else:
            # Verificar credenciales R2
            r2_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
            r2_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            r2_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            r2_secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            
            if not all([r2_endpoint, r2_bucket, r2_key, r2_secret]):
                issues.append("ERROR: Cloudflare R2 no configurado completamente")
            else:
                success.append("OK: Cloudflare R2 configurado")
                
                # Test de conectividad R2
                try:
                    from core.r2_config import R2HealthCheck
                    connectivity, msg = R2HealthCheck.check_connectivity()
                    if connectivity:
                        success.append("OK: R2 conectividad OK")
                    else:
                        issues.append(f"ERROR: R2 conectividad falló: {msg}")
                except Exception as e:
                    warnings.append(f"WARNING: No se pudo verificar R2: {e}")
        
        # 5. Verificar Base de Datos
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine.lower():
            warnings.append("WARNING: Usando SQLite - Recomendado PostgreSQL para producción")
        elif 'postgresql' in db_engine.lower() or 'psycopg' in db_engine.lower():
            success.append("OK: Base de datos PostgreSQL")
        else:
            success.append(f"OK: Base de datos: {db_engine}")
        
        # 6. Verificar Redis
        redis_url = os.environ.get('REDIS_URL')
        if redis_url and 'localhost' not in redis_url:
            success.append("OK: Redis configurado")
        elif redis_url:
            warnings.append("WARNING: Redis apunta a localhost - Verificar en producción")
        else:
            warnings.append("WARNING: Redis no configurado - Recomendado para caché")
        
        # 7. Verificar Email
        resend_key = os.environ.get('RESEND_API_KEY')
        if resend_key and resend_key != 'your-resend-api-key':
            success.append("OK: Email (Resend) configurado")
        else:
            warnings.append("WARNING: Email no configurado - Funcionalidades limitadas")
        
        # 8. Verificar configuración de archivos grandes
        max_file_size = int(os.environ.get('MAX_FILE_SIZE_MB', 600))
        if max_file_size >= 1200:
            success.append(f"OK: Archivos grandes habilitados ({max_file_size}MB)")
        else:
            warnings.append(f"WARNING: MAX_FILE_SIZE_MB={max_file_size} - Considera aumentar a 1200MB")
        
        # 9. Verificar límite HTTP
        http_limit = settings.DATA_UPLOAD_MAX_NUMBER_SIZE
        if http_limit >= 1342177280:  # 1.25GB
            success.append("OK: Límite HTTP optimizado (1.25GB)")
        else:
            warnings.append(f"WARNING: DATA_UPLOAD_MAX_NUMBER_SIZE bajo - Aumentar a 1342177280")
        
        # 10. Verificar HTTPS
        if not settings.DEBUG:
            secure_ssl = getattr(settings, 'SECURE_SSL_REDIRECT', False)
            if secure_ssl:
                success.append("OK: HTTPS redirect activado")
            else:
                warnings.append("WARNING: SECURE_SSL_REDIRECT=False - Activar para producción")
        
        # Imprimir resultados
        self.stdout.write("\n" + "="*60)
        self.stdout.write("RESULTADOS DE VERIFICACIÓN")
        self.stdout.write("="*60 + "\n")
        
        if success:
            self.stdout.write(self.style.SUCCESS("\nCONFIGURACIONES CORRECTAS:\n"))
            for item in success:
                self.stdout.write(f"   {item}")
        
        if warnings:
            self.stdout.write(self.style.WARNING("\nADVERTENCIAS:\n"))
            for item in warnings:
                self.stdout.write(f"   {item}")
        
        if issues:
            self.stdout.write(self.style.ERROR("\nPROBLEMAS CRÍTICOS:\n"))
            for item in issues:
                self.stdout.write(f"   {item}")
        
        # Resumen final
        self.stdout.write("\n" + "="*60)
        
        total = len(success) + len(warnings) + len(issues)
        score = (len(success) / total * 100) if total > 0 else 0
        
        self.stdout.write(f"\nPUNTUACIÓN: {score:.0f}%")
        self.stdout.write(f"   Correctas: {len(success)}")
        self.stdout.write(f"   Advertencias: {len(warnings)}")
        self.stdout.write(f"   Críticas: {len(issues)}")
        
        if issues:
            self.stdout.write(self.style.ERROR("\nNO LISTO PARA PRODUCCIÓN"))
            self.stdout.write("   Resuelve los problemas críticos antes de desplegar.\n")
            sys.exit(1)
        elif warnings:
            self.stdout.write(self.style.WARNING("\nLISTO CON ADVERTENCIAS"))
            self.stdout.write("   Puedes desplegar pero revisa las advertencias.\n")
        else:
            self.stdout.write(self.style.SUCCESS("\nLISTO PARA PRODUCCIÓN"))
            self.stdout.write("   ¡Todos los checks pasaron!\n")
        
        # Próximos pasos
        if issues or warnings:
            self.stdout.write("\n" + "="*60)
            self.stdout.write("PRÓXIMOS PASOS:")
            self.stdout.write("="*60 + "\n")
            
            if issues:
                self.stdout.write("\n1. Resolver problemas críticos:")
                self.stdout.write("   - Configurar variables de entorno de producción")
                self.stdout.write("   - Ver: CHECKLIST_MVP_PRODUCCION.md\n")
            
            if warnings:
                self.stdout.write("\n2. Revisar advertencias:")
                self.stdout.write("   - Configurar servicios opcionales")
                self.stdout.write("   - Mejorar configuración para producción\n")
        
        self.stdout.write("="*60 + "\n")

