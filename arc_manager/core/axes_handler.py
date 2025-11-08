"""
Custom AXES handler para logging de eventos de seguridad.
Mejora el comportamiento por defecto de Axes con logging estructurado.
"""
from axes.handlers.database import AxesDatabaseHandler
import logging

logger = logging.getLogger('apps.accounts')


class CustomAxesHandler(AxesDatabaseHandler):
    """
    Handler personalizado que agrega logging de seguridad crítico.
    
    Hereda de AxesDatabaseHandler para usar la BD como backend de almacenamiento.
    Sobrescribe métodos clave para agregar logs útiles.
    """
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente considerando proxies"""
        if not request:
            return 'Desconocida'
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')
        return ip
    
    def user_login_failed(self, sender, credentials, request=None, **kwargs):
        """
        Se ejecuta cuando un login falla.
        Incrementa el contador de intentos fallidos.
        """
        # Llamar al método padre para registrar el fallo
        result = super().user_login_failed(sender, credentials, request, **kwargs)
        
        # Obtener información del intento
        username = credentials.get('username', 'N/A')
        ip_address = self.get_client_ip(request)
        
        # Log del intento fallido (ya se hace en views.py, aquí es redundante)
        # Solo logueamos si está cerca del límite
        from axes.helpers import get_failure_limit
        
        try:
            failure_limit = get_failure_limit(request, credentials)
            attempts = self.get_failures(request, credentials)
            
            if attempts >= failure_limit - 2:  # Log cuando quedan 2 intentos o menos
                logger.warning(
                    f"ALERTA BLOQUEO INMINENTE | Email: {username} | IP: {ip_address} | "
                    f"Intentos: {attempts}/{failure_limit}"
                )
        except Exception as e:
            logger.error(f"Error en user_login_failed handler | Error: {str(e)}")
        
        return result
    
    def user_locked_out(self, sender, request, credentials, **kwargs):
        """
        Se ejecuta cuando un usuario es bloqueado por exceder intentos.
        CRÍTICO: Este es el log de seguridad más importante.
        """
        # Llamar al método padre
        result = super().user_locked_out(sender, request, credentials, **kwargs)
        
        # Obtener información del bloqueo
        username = credentials.get('username', 'N/A')
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200] if request else 'N/A'
        
        # Log CRÍTICO de seguridad (nivel WARNING para alertas)
        logger.warning(
            f"USUARIO BLOQUEADO POR FUERZA BRUTA | Email: {username} | "
            f"IP: {ip_address} | User-Agent: {user_agent}"
        )
        
        return result

