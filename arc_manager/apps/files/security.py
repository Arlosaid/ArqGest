# apps/files/security.py
"""
Utilidades de seguridad para el módulo de archivos
"""
import os
import hashlib
import logging
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class FileSecurityManager:
    """Gestión de seguridad para archivos"""
    
    @classmethod
    def get_rate_limits(cls):
        """Obtener límites de rate limiting desde la configuración del sistema"""
        from apps.main.models import SystemSettings
        sys_settings = SystemSettings.load()
        return {
            'requests_per_minute': sys_settings.upload_requests_per_minute,
            'requests_per_hour': sys_settings.upload_requests_per_hour,
            'total_size_per_hour_mb': sys_settings.upload_size_per_hour_mb
        }
    
    @classmethod
    def check_upload_rate_limit(cls, user, file_size_bytes=0):
        """
        Verificar límites de rate limiting para uploads
        """
        user_id = user.id
        now = timezone.now()
        
        # Obtener límites dinámicos desde la configuración
        rate_limits = cls.get_rate_limits()
        
        # Claves de caché para rate limiting
        minute_key = f"upload_rate_minute_{user_id}_{now.minute}"
        hour_key = f"upload_rate_hour_{user_id}_{now.hour}"
        size_hour_key = f"upload_size_hour_{user_id}_{now.hour}"
        
        # Verificar requests por minuto
        minute_count = cache.get(minute_key, 0)
        if minute_count >= rate_limits['requests_per_minute']:
            return False, "Demasiados uploads por minuto. Espera un momento."
        
        # Verificar requests por hora
        hour_count = cache.get(hour_key, 0)
        if hour_count >= rate_limits['requests_per_hour']:
            return False, "Límite de uploads por hora alcanzado."
        
        # Verificar tamaño total por hora
        hour_size_mb = cache.get(size_hour_key, 0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        if (hour_size_mb + file_size_mb) > rate_limits['total_size_per_hour_mb']:
            return False, f"Límite de tamaño por hora alcanzado ({rate_limits['total_size_per_hour_mb']}MB = {rate_limits['total_size_per_hour_mb']/1000:.1f}GB)."
        
        # Incrementar contadores
        cache.set(minute_key, minute_count + 1, 60)  # 1 minuto
        cache.set(hour_key, hour_count + 1, 3600)  # 1 hora
        cache.set(size_hour_key, hour_size_mb + file_size_mb, 3600)  # 1 hora
        
        return True, None
    
    @classmethod
    def check_suspicious_activity(cls, user, request):
        """
        Detectar actividad sospechosa
        """
        user_id = user.id
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        suspicious_indicators = []
        
        # 1. Múltiples IPs en poco tiempo
        ip_key = f"user_ips_{user_id}"
        user_ips = cache.get(ip_key, set())
        if isinstance(user_ips, set):
            user_ips.add(ip)
            if len(user_ips) > 5:  # Más de 5 IPs diferentes en 1 hora
                suspicious_indicators.append("multiple_ips")
            cache.set(ip_key, user_ips, 3600)
        
        # 2. User-Agent sospechoso
        suspicious_agents = ['curl', 'wget', 'python-requests', 'bot', 'crawler']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            suspicious_indicators.append("suspicious_user_agent")
        
        # 3. Uploads muy rápidos (posible automatización)
        rapid_key = f"rapid_uploads_{user_id}"
        rapid_count = cache.get(rapid_key, 0)
        if rapid_count > 20:  # Más de 20 uploads en 5 minutos
            suspicious_indicators.append("rapid_uploads")
        cache.set(rapid_key, rapid_count + 1, 300)  # 5 minutos
        
        if suspicious_indicators:
            logger.warning(
                f"Suspicious activity detected for user {user.email}: {suspicious_indicators}"
            )
            return True, suspicious_indicators
        
        return False, []
    
    @classmethod
    def sanitize_filename(cls, filename):
        """
        Sanitizar nombre de archivo para evitar path traversal
        """
        # Remover caracteres peligrosos
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limitar longitud
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized
    
    @classmethod
    def generate_secure_filename(cls, original_filename):
        """
        Generar nombre de archivo seguro con hash
        """
        # Obtener extensión original
        _, ext = os.path.splitext(original_filename)
        
        # Generar hash único basado en timestamp y filename
        timestamp = timezone.now().isoformat()
        content = f"{original_filename}_{timestamp}"
        hash_name = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return f"{hash_name}{ext}"
    
    @classmethod
    def check_file_quarantine(cls, file_path):
        """
        Verificar si un archivo está en cuarentena
        """
        quarantine_key = f"quarantine_{hashlib.md5(file_path.encode()).hexdigest()}"
        return cache.get(quarantine_key, False)
    
    @classmethod
    def quarantine_file(cls, file_path, reason, duration_hours=24):
        """
        Poner archivo en cuarentena
        """
        quarantine_key = f"quarantine_{hashlib.md5(file_path.encode()).hexdigest()}"
        quarantine_data = {
            'reason': reason,
            'quarantined_at': timezone.now().isoformat(),
            'file_path': file_path
        }
        
        cache.set(quarantine_key, quarantine_data, duration_hours * 3600)
        
        logger.warning(f"File quarantined: {file_path} - Reason: {reason}")
    
    @classmethod
    def log_security_event(cls, event_type, user, details):
        """
        Registrar evento de seguridad
        """
        # FIXME: Migrar a structured_logging después del deploy
        # from core.structured_logging import log_security_event
        
        # FIXME: Función temporal hasta migrar a structured_logging
        def log_operation(*args, **kwargs):
            """Temporal stub para evitar errores durante deploy"""
            pass
        
        log_operation(
            f'FILE_SECURITY_{event_type}',
            user.email if user else 'system',
            logger,
            level='WARNING',
            **details
        )


class FileIntegrityChecker:
    """Verificación de integridad de archivos"""
    
    @classmethod
    def verify_file_integrity(cls, file_obj):
        """
        Verificar integridad del archivo usando checksum
        """
        if not file_obj.checksum_sha256:
            return True, "No checksum available"
        
        try:
            # Calcular checksum actual
            hasher = hashlib.sha256()
            with file_obj.file.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            current_checksum = hasher.hexdigest()
            
            if current_checksum == file_obj.checksum_sha256:
                return True, "File integrity verified"
            else:
                return False, "File integrity compromised - checksum mismatch"
                
        except Exception as e:
            return False, f"Error verifying integrity: {str(e)}"
    
    @classmethod
    def batch_integrity_check(cls, queryset):
        """
        Verificación de integridad en lote
        """
        results = {
            'verified': 0,
            'corrupted': 0,
            'errors': 0,
            'corrupted_files': []
        }
        
        for file_obj in queryset:
            is_valid, message = cls.verify_file_integrity(file_obj)
            
            if is_valid:
                results['verified'] += 1
            elif "checksum mismatch" in message:
                results['corrupted'] += 1
                results['corrupted_files'].append({
                    'id': file_obj.id,
                    'filename': file_obj.filename,
                    'path': file_obj.file.name
                })
            else:
                results['errors'] += 1
        
        return results


def check_file_permissions(user, file_obj, action='view'):
    """
    Verificar permisos de archivo
    """
    # Superusuario tiene todos los permisos
    if user.is_superuser:
        return True
    
    # Verificar que el usuario pertenece a la misma organización
    if not user.organization:
        return False
    
    if file_obj.phase.project.organization != user.organization:
        return False
    
    # Verificaciones adicionales por acción
    if action == 'delete':
        # Solo el usuario que subió el archivo o admin puede eliminarlo
        if file_obj.uploaded_by != user and not user.is_staff:
            return False
    
    return True


def get_secure_file_url(file_obj, user, expires_in=3600):
    """
    Generar URL segura temporal para descarga
    """
    if not check_file_permissions(user, file_obj):
        return None
    
    # Generar token temporal
    timestamp = int(timezone.now().timestamp())
    expires = timestamp + expires_in
    
    token_data = f"{file_obj.id}_{user.id}_{expires}"
    token = hashlib.sha256(
        f"{token_data}_{settings.SECRET_KEY}".encode()
    ).hexdigest()[:16]
    
    # Guardar en caché
    cache_key = f"file_token_{token}"
    cache.set(cache_key, {
        'file_id': file_obj.id,
        'user_id': user.id,
        'expires': expires
    }, expires_in)
    
    return f"/files/secure/{file_obj.id}/{token}/"
