# apps/main/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache


class BaseSingletonSettings(models.Model):
    """Clase base para modelos de configuración singleton"""
    
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    updated_by = models.CharField("Actualizado por", max_length=255, blank=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        self._clear_cache()
    
    def delete(self, *args, **kwargs):
        pass
    
    def _clear_cache(self):
        cache_key = f'{self.__class__.__name__.lower()}_settings'
        cache.delete(cache_key)
    
    @classmethod
    def load(cls):
        cache_key = f'{cls.__name__.lower()}_settings'
        settings = cache.get(cache_key)
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, settings, 3600)
        return settings


class UserLimitsSettings(models.Model):
    """Límites de usuarios por plan - REQUIERE SINCRONIZACIÓN"""
    
    default_max_users = models.PositiveIntegerField(
        "Máximo de usuarios (por defecto)",
        default=5,
        help_text="Límite por defecto de usuarios para nuevos planes"
    )
    
    max_users_trial = models.PositiveIntegerField(
        "Máximo de usuarios (Trial)",
        default=1,
        help_text="Límite de usuarios para planes de prueba gratuita"
    )
    
    max_users_basic = models.PositiveIntegerField(
        "Máximo de usuarios (Plan Básico)",
        default=5,
        help_text="Límite de usuarios para el plan básico"
    )
    
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    updated_by = models.CharField("Actualizado por", max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Límites de Usuarios"
        verbose_name_plural = "Límites de Usuarios"
    
    def __str__(self):
        return f"Límites de Usuarios (Trial: {self.max_users_trial}, Básico: {self.max_users_basic})"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('userlimitssettings_settings')
    
    def delete(self, *args, **kwargs):
        pass
    
    @classmethod
    def load(cls):
        cache_key = 'userlimitssettings_settings'
        settings = cache.get(cache_key)
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, settings, 3600)
        return settings


class StorageLimitsSettings(models.Model):
    """Límites de almacenamiento por plan - REQUIERE SINCRONIZACIÓN"""
    
    default_storage_gb = models.PositiveIntegerField(
        "Almacenamiento por defecto (GB)",
        default=75,
        help_text="Límite de almacenamiento por defecto para nuevos planes"
    )
    
    storage_trial_gb = models.PositiveIntegerField(
        "Almacenamiento Trial (GB)",
        default=10,
        help_text="Límite de almacenamiento para planes de prueba gratuita"
    )
    
    storage_basic_gb = models.PositiveIntegerField(
        "Almacenamiento Plan Básico (GB)",
        default=75,
        help_text="Límite de almacenamiento para el plan básico"
    )
    
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    updated_by = models.CharField("Actualizado por", max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Límites de Almacenamiento"
        verbose_name_plural = "Límites de Almacenamiento"
    
    def __str__(self):
        return f"Límites de Almacenamiento (Trial: {self.storage_trial_gb}GB, Básico: {self.storage_basic_gb}GB)"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('storagelimitssettings_settings')
    
    def delete(self, *args, **kwargs):
        pass
    
    @classmethod
    def load(cls):
        cache_key = 'storagelimitssettings_settings'
        settings = cache.get(cache_key)
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, settings, 3600)
        return settings


class FileLimitsSettings(models.Model):
    """Límites de archivos - APLICACIÓN INMEDIATA"""
    
    max_file_size_mb = models.PositiveIntegerField(
        "Tamaño máximo de archivo (MB)",
        default=500,
        help_text="Tamaño máximo permitido por archivo individual"
    )
    
    # DEPRECADO: La aplicación solo permite 1 archivo a la vez
    # Mantenido para compatibilidad con migraciones existentes
    max_upload_size_per_request_mb = models.PositiveIntegerField(
        "Tamaño máximo por solicitud (MB) [DEPRECADO]",
        default=2000,
        help_text="[DEPRECADO] Este campo ya no se utiliza. La app solo permite 1 archivo a la vez.",
        editable=False  # Ocultar de formularios de admin
    )
    
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    updated_by = models.CharField("Actualizado por", max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Límites de Archivos"
        verbose_name_plural = "Límites de Archivos"
    
    def __str__(self):
        return f"Límites de Archivos (Max: {self.max_file_size_mb}MB por archivo)"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('filelimitssettings_settings')
    
    def delete(self, *args, **kwargs):
        pass
    
    @classmethod
    def load(cls):
        cache_key = 'filelimitssettings_settings'
        settings = cache.get(cache_key)
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, settings, 3600)
        return settings


class PlanBillingSettings(models.Model):
    """Configuración de planes y facturación - REQUIERE SINCRONIZACIÓN"""
    
    trial_duration_days = models.PositiveIntegerField(
        "Duración del trial (días)",
        default=30,
        help_text="Duración en días del período de prueba gratuita"
    )
    
    billing_cycle_days = models.PositiveIntegerField(
        "Ciclo de facturación (días)",
        default=30,
        help_text="Duración estándar del ciclo de facturación"
    )
    
    grace_period_days = models.PositiveIntegerField(
        "Período de gracia (días)",
        default=7,
        help_text="Días de gracia después de que expire una suscripción"
    )
    
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    updated_by = models.CharField("Actualizado por", max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Configuración de Planes y Facturación"
        verbose_name_plural = "Configuración de Planes y Facturación"
    
    def __str__(self):
        return f"Planes (Trial: {self.trial_duration_days}d, Ciclo: {self.billing_cycle_days}d)"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('planbillingsettings_settings')
    
    def delete(self, *args, **kwargs):
        pass
    
    @classmethod
    def load(cls):
        cache_key = 'planbillingsettings_settings'
        settings = cache.get(cache_key)
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set(cache_key, settings, 3600)
        return settings


class SystemSettings(models.Model):
    """
    Configuraciones globales del sistema que pueden ser modificadas desde el admin.
    Solo puede existir una instancia de este modelo (patrón Singleton).
    
    NOTA: Para modificar límites de usuarios y almacenamiento por plan,
    edita directamente cada Plan desde el admin de Planes.
    """
    
    # === LÍMITES DE ARCHIVOS ===
    max_file_size_mb = models.PositiveIntegerField(
        "Tamaño máximo de archivo (MB)",
        default=1500,
        help_text="Tamaño máximo permitido por archivo individual. Se aplica inmediatamente al guardar."
    )
    
    # Configuración técnica de uploads (simplificado desde variables de entorno)
    data_upload_max_memory_mb = models.PositiveIntegerField(
        "Memoria máxima para uploads (MB)",
        default=25,
        help_text="Tamaño máximo de archivos que se procesan en memoria RAM (recomendado: 25 MB)"
    )
    
    max_checksum_size_mb = models.PositiveIntegerField(
        "Tamaño máximo para checksum (MB)",
        default=50,
        help_text="Tamaño máximo de archivo para calcular checksums SHA256 (evita sobrecarga en archivos grandes)"
    )
    
    # === CONFIGURACIÓN AVANZADA DE UPLOADS ===
    # Configuración de chunks para archivos grandes
    upload_chunk_size_mb = models.PositiveIntegerField(
        "Tamaño de chunk (MB)",
        default=50,
        help_text="Tamaño de cada chunk al subir archivos grandes. Mayor = más rápido pero más memoria"
    )
    
    upload_max_concurrency = models.PositiveIntegerField(
        "Concurrencia máxima",
        default=15,
        help_text="Número de chunks que se suben simultáneamente. Mayor = más rápido pero más ancho de banda"
    )
    
    upload_retry_attempts = models.PositiveIntegerField(
        "Intentos de retry",
        default=3,
        help_text="Número de reintentos si falla un chunk"
    )
    
    upload_timeout_minutes = models.PositiveIntegerField(
        "Timeout de upload (minutos)",
        default=30,
        help_text="Tiempo máximo para completar un upload antes de cancelar"
    )
    
    # Configuración para móviles
    upload_chunk_size_mobile_mb = models.PositiveIntegerField(
        "Tamaño de chunk móvil (MB)",
        default=10,
        help_text="Tamaño de chunk para dispositivos móviles (más pequeño = más estable)"
    )
    
    upload_max_concurrency_mobile = models.PositiveIntegerField(
        "Concurrencia móvil",
        default=2,
        help_text="Concurrencia para móviles (menor = más estable en conexiones lentas)"
    )
    
    upload_max_file_size_mobile_mb = models.PositiveIntegerField(
        "Tamaño máximo móvil (MB)",
        default=200,
        help_text="Tamaño máximo de archivo para uploads desde móvil"
    )
    
    # === CONFIGURACIÓN DE CACHÉ ===
    cache_timeout_seconds = models.PositiveIntegerField(
        "Tiempo de caché (segundos)",
        default=300,
        help_text="Tiempo en segundos para mantener datos en caché (300 = 5 minutos)"
    )
    
    storage_cache_timeout = models.PositiveIntegerField(
        "Tiempo de caché de almacenamiento (segundos)",
        default=180,
        help_text="Tiempo en segundos para cachear cálculos de almacenamiento"
    )
    
    # === CONFIGURACIÓN DE SESIONES ===
    session_timeout_minutes = models.PositiveIntegerField(
        "Timeout de sesión (minutos)",
        default=60,
        help_text="Tiempo en minutos antes de que expire una sesión inactiva"
    )
    
    # === RATE LIMITING ===
    upload_requests_per_minute = models.PositiveIntegerField(
        "Uploads por minuto",
        default=15,
        help_text="Número máximo de uploads permitidos por minuto por usuario"
    )
    
    upload_requests_per_hour = models.PositiveIntegerField(
        "Uploads por hora",
        default=200,
        help_text="Número máximo de uploads permitidos por hora por usuario"
    )
    
    upload_size_per_hour_mb = models.PositiveIntegerField(
        "Tamaño total de uploads por hora (MB)",
        default=5000,
        help_text="Tamaño máximo acumulado de uploads por hora (en MB)"
    )
    
    # === MODO MANTENIMIENTO ===
    maintenance_mode = models.BooleanField(
        "Modo mantenimiento",
        default=False,
        help_text="Activar para poner el sitio en modo mantenimiento (solo admin puede acceder)"
    )
    
    maintenance_message = models.TextField(
        "Mensaje de mantenimiento",
        blank=True,
        default="El sistema está en mantenimiento. Volveremos pronto.",
        help_text="Mensaje que verán los usuarios durante el mantenimiento"
    )
    
    # === CONTACTO Y SOPORTE ===
    support_email = models.EmailField(
        "Email de soporte",
        blank=True,
        default="soporte@arcmanager.com",
        help_text="Email de contacto para soporte técnico"
    )
    
    company_name = models.CharField(
        "Nombre de la empresa",
        max_length=200,
        default="ARC Manager",
        help_text="Nombre de la empresa que aparecerá en el sistema"
    )
    
    # === NOTIFICACIONES ===
    enable_email_notifications = models.BooleanField(
        "Habilitar notificaciones por email",
        default=True,
        help_text="Activar/desactivar envío de notificaciones por correo"
    )
    
    low_storage_warning_percentage = models.PositiveIntegerField(
        "Advertencia de almacenamiento bajo (%)",
        default=80,
        help_text="Porcentaje de uso de almacenamiento para mostrar advertencia"
    )
    
    # === METADATA ===
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
    
    def __str__(self):
        return f"Configuración del Sistema (actualizado: {self.updated_at.strftime('%d/%m/%Y %H:%M')})"
    
    def save(self, *args, **kwargs):
        """
        Guardar configuración del sistema.
        Limpia caché para asegurar que los cambios se reflejen.
        """
        self.pk = 1  # Asegurar singleton
        super().save(*args, **kwargs)
        
        # Limpiar caché de SystemSettings
        cache.delete('system_settings')
    
    def delete(self, *args, **kwargs):
        """Prevenir eliminación de la configuración"""
        pass
    
    @classmethod
    def load(cls):
        """
        Cargar la configuración del sistema (con caché de 1 hora).
        Crea una instancia por defecto si no existe.
        
        El caché se limpia automáticamente al guardar cambios.
        """
        settings = cache.get('system_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            if created:
                settings.save()  # Guardar valores por defecto
            cache.set('system_settings', settings, 3600)  # 1 hora
        return settings
    
    @classmethod
    def get_setting(cls, setting_name, default=None):
        """Obtener un valor específico de configuración"""
        settings = cls.load()
        return getattr(settings, setting_name, default)
    
    def get_max_file_size_bytes(self):
        """Retorna el tamaño máximo de archivo en bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    def get_data_upload_max_number_bytes(self):
        """
        Retorna el límite máximo de tamaño HTTP request en bytes.
        Debe ser mayor que max_file_size para permitir overhead HTTP.
        """
        # Agregar 25% de overhead para headers HTTP, metadata, etc.
        return int(self.max_file_size_mb * 1024 * 1024 * 1.25)
    
    def get_data_upload_max_memory_bytes(self):
        """Retorna el límite de memoria para uploads en bytes"""
        return self.data_upload_max_memory_mb * 1024 * 1024
    
    def get_max_checksum_size_bytes(self):
        """Retorna el tamaño máximo para calcular checksums en bytes"""
        return self.max_checksum_size_mb * 1024 * 1024
    
    def get_upload_size_per_hour_bytes(self):
        """Retorna el límite de tamaño de uploads por hora en bytes"""
        return self.upload_size_per_hour_mb * 1024 * 1024
    
    def is_storage_warning(self, usage_percentage):
        """Verifica si el porcentaje de uso requiere advertencia"""
        return usage_percentage >= self.low_storage_warning_percentage
    
    def get_upload_config(self, device_type='desktop', connection_type='broadband'):
        """
        Obtiene la configuración optimizada de uploads basada en el contexto.
        
        Args:
            device_type: 'desktop', 'tablet', 'mobile'
            connection_type: 'broadband', 'mobile', 'slow'
        
        Returns:
            dict: Configuración optimizada para el contexto dado
        """
        is_mobile = device_type == 'mobile' or connection_type == 'mobile'
        is_slow = connection_type == 'slow'
        
        if is_mobile:
            return {
                'chunk_size_mb': self.upload_chunk_size_mobile_mb,
                'max_concurrent_uploads': self.upload_max_concurrency_mobile,
                'retry_attempts': self.upload_retry_attempts + 2,  # Más retries en móvil
                'timeout_minutes': self.upload_timeout_minutes + 15,  # Más tiempo en móvil
                'recommended_max_file_size_mb': self.upload_max_file_size_mobile_mb
            }
        elif is_slow:
            return {
                'chunk_size_mb': 5,  # Chunks muy pequeños
                'max_concurrent_uploads': 1,  # Sin concurrencia
                'retry_attempts': self.upload_retry_attempts + 5,  # Muchos retries
                'timeout_minutes': self.upload_timeout_minutes * 2,  # Doble de tiempo
                'recommended_max_file_size_mb': 100
            }
        else:  # broadband/desktop - configuración óptima
            return {
                'chunk_size_mb': self.upload_chunk_size_mb,
                'max_concurrent_uploads': self.upload_max_concurrency,
                'retry_attempts': self.upload_retry_attempts,
                'timeout_minutes': self.upload_timeout_minutes,
                'recommended_max_file_size_mb': self.max_file_size_mb
            }
    
    def get_upload_chunk_size_bytes(self, is_mobile=False):
        """Retorna el tamaño de chunk en bytes según el tipo de dispositivo"""
        chunk_size_mb = self.upload_chunk_size_mobile_mb if is_mobile else self.upload_chunk_size_mb
        return chunk_size_mb * 1024 * 1024
