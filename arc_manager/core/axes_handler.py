"""
Custom AXES handler para logs más claros y útiles
"""
from axes.handlers.database import AxesDatabaseHandler
import logging

logger = logging.getLogger('axes.watch_login')


class CustomAxesHandler(AxesDatabaseHandler):
    """
    Handler personalizado para AXES con logs más informativos
    """
    
    def user_login_failed(self, sender, credentials, request=None, **kwargs):
        """Override para loguear información útil cuando falla un login"""
        # Primero ejecutar el comportamiento original
        result = super().user_login_failed(sender, credentials, request, **kwargs)
        
        if request:
            # Obtener información útil
            username = credentials.get('username', 'unknown')
            ip_address = self.get_client_ip_address(request)
            user_agent = self.get_client_user_agent(request)[:100]
            attempt_count = self.get_failure_count(request, credentials)
            
            # Log claro y directo
            logger.warning(
                f"Login fallido #{attempt_count} - Usuario: {username}, "
                f"IP: {ip_address}, "
                f"User-Agent: {user_agent}"
            )
            
            # Si está cerca del límite, advertir
            from django.conf import settings
            failure_limit = getattr(settings, 'AXES_FAILURE_LIMIT', 10)
            if attempt_count >= failure_limit - 2:
                logger.warning(
                    f"⚠️ ALERTA: Usuario {username} cerca del bloqueo "
                    f"({attempt_count}/{failure_limit} intentos)"
                )
        
        return result
    
    def user_locked_out(self, sender, request, credentials, **kwargs):
        """Override para loguear cuando se bloquea un usuario"""
        # Primero ejecutar el comportamiento original
        result = super().user_locked_out(sender, request, credentials, **kwargs)
        
        if request:
            username = credentials.get('username', 'unknown')
            ip_address = self.get_client_ip_address(request)
            
            # Log CRÍTICO para bloqueos
            logger.error(
                f"🔒 USUARIO BLOQUEADO - Usuario: {username}, "
                f"IP: {ip_address}, "
                f"Razón: Superado límite de intentos fallidos"
            )
        
        return result
