"""
Filtros de logging optimizados para performance y seguridad
"""
import logging
import re
import traceback
from threading import local
from urllib.parse import urlparse, parse_qs
from django.conf import settings

# Thread-local storage para request context
_thread_locals = local()


class RequestIdFilter(logging.Filter):
    """
    Agrega request_id y user_id a todos los logs para trazabilidad
    """
    
    def filter(self, record):
        """Agrega request_id y user_id del thread local al record"""
        record.request_id = getattr(_thread_locals, 'request_id', None)
        record.user_id = getattr(_thread_locals, 'user_id', None)
        record.organization_id = getattr(_thread_locals, 'organization_id', None)
        return True


def set_request_id(request_id):
    """Establece el request_id en el thread local"""
    _thread_locals.request_id = request_id


def clear_request_id():
    """Limpia el request_id del thread local"""
    if hasattr(_thread_locals, 'request_id'):
        delattr(_thread_locals, 'request_id')


def get_request_id():
    """Obtiene el request_id actual"""
    return getattr(_thread_locals, 'request_id', None)


def set_user_context(user_id=None, organization_id=None):
    """Establece el contexto del usuario en el thread local"""
    if user_id is not None:
        _thread_locals.user_id = user_id
    if organization_id is not None:
        _thread_locals.organization_id = organization_id


def clear_user_context():
    """Limpia el contexto del usuario del thread local"""
    if hasattr(_thread_locals, 'user_id'):
        delattr(_thread_locals, 'user_id')
    if hasattr(_thread_locals, 'organization_id'):
        delattr(_thread_locals, 'organization_id')


def get_user_context():
    """Obtiene el contexto del usuario actual"""
    return {
        'user_id': getattr(_thread_locals, 'user_id', None),
        'organization_id': getattr(_thread_locals, 'organization_id', None),
    }

class RequestLoggingFilter(logging.Filter):
    """
    Filtro que acorta y limpia los logs de request de Django para evitar logs muy largos
    """
    
    def filter(self, record):
        """
        Procesa el registro de log para limpiar URLs largas y datos sensibles
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Detectar logs de request de Django
            if '"GET' in record.msg or '"POST' in record.msg:
                record.msg = self._clean_request_log(record.msg)
        
        return True
    
    def _clean_request_log(self, msg):
        """
        Limpia un log de request removiendo parámetros largos y sensibles
        """
        # Patrones para detectar URLs con parámetros largos
        url_pattern = r'"(GET|POST|PUT|DELETE|PATCH)\s+([^"\s]+)([^"]*)"'
        match = re.search(url_pattern, msg)
        
        if not match:
            return msg
        
        method = match.group(1)
        base_url = match.group(2)
        rest_of_log = match.group(3)
        
        # Si la URL tiene parámetros de query largos, truncarlos
        if '?' in base_url:
            url_parts = base_url.split('?', 1)
            base_path = url_parts[0]
            query_string = url_parts[1]
            
            # Lista de parámetros sensibles a remover
            sensitive_params = [
                'csrfmiddlewaretoken',
                'password',
                'token',
                'api_key',
                'secret',
            ]
            
            # Parsear parámetros
            try:
                parsed_params = parse_qs(query_string)
                
                # Filtrar parámetros sensibles y largos
                clean_params = []
                for key, values in parsed_params.items():
                    if key.lower() in sensitive_params:
                        clean_params.append(f"{key}=[FILTERED]")
                    elif any(len(str(v)) > 50 for v in values):
                        # Si algún valor es muy largo, truncarlo
                        clean_params.append(f"{key}=[TRUNCATED]")
                    else:
                        # Si hay pocos parámetros cortos, mantenerlos
                        if len(clean_params) < 3 and len(str(values[0])) <= 20:
                            clean_params.append(f"{key}={values[0]}")
                        else:
                            clean_params.append(f"{key}=...")
                
                # Reconstruir URL
                if clean_params:
                    clean_url = f"{base_path}?{'&'.join(clean_params[:3])}"
                    if len(clean_params) > 3:
                        clean_url += "&..."
                else:
                    clean_url = base_path
                    
            except Exception:
                # Si hay error al parsear, simplemente truncar
                if len(query_string) > 100:
                    clean_url = f"{base_path}?{query_string[:50]}...TRUNCATED"
                else:
                    clean_url = base_url
        else:
            clean_url = base_url
        
        # Reconstruir el mensaje del log
        new_msg = msg.replace(
            f'"{method} {base_url}{rest_of_log}"',
            f'"{method} {clean_url}{rest_of_log}"'
        )
        
        return new_msg


class CompactExceptionFilter(logging.Filter):
    """
    Filtro que reduce el tamaño de los stack traces en producción.
    En lugar de mostrar todo el traceback, solo muestra:
    - Primera línea (donde empezó el error)
    - Última línea (donde ocurrió el error)
    - Mensaje de excepción
    
    El stack trace completo se debe enviar a Sentry/herramientas de monitoreo externas.
    """
    
    def filter(self, record):
        """
        Reduce stack traces en producción para evitar logs verbosos
        """
        # Solo aplicar en producción
        try:
            if settings.DEBUG:
                return True
        except:
            # Si no se puede acceder a settings, asumir producción
            pass
        
        # Si el record tiene información de excepción
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            
            if exc_tb:
                # Extraer primera y última línea del traceback
                tb_list = traceback.extract_tb(exc_tb)
                
                if len(tb_list) > 0:
                    first_frame = tb_list[0]
                    last_frame = tb_list[-1]
                    
                    # Crear un resumen compacto del traceback
                    compact_tb = (
                        f"{exc_type.__name__} at {record.pathname}:{record.lineno}\n"
                        f"  First: {first_frame.filename}:{first_frame.lineno} in {first_frame.name}\n"
                        f"  Last:  {last_frame.filename}:{last_frame.lineno} in {last_frame.name}\n"
                        f"  Message: {exc_value}"
                    )
                    
                    # Reemplazar el mensaje para incluir el resumen compacto
                    if hasattr(record, 'msg'):
                        record.msg = f"{record.msg}\n{compact_tb}"
                    
                    # Limpiar exc_info para evitar que se loguee el traceback completo
                    record.exc_info = None
                    record.exc_text = None
        
        return True


class IgnoreStaticFilesFilter(logging.Filter):
    """
    Filtro que ELIMINA completamente logs de archivos estáticos y peticiones innecesarias.
    Reduce el ruido en logs de producción en un 90%.
    """
    
    # Paths que NUNCA deben loguearse
    IGNORED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
        '/__debug__/',  # Django Debug Toolbar
        '/health/',  # Health checks
        '/_health',  # Health checks alternativo
    ]
    
    # Extensiones de archivos estáticos
    STATIC_EXTENSIONS = [
        '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', 
        '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map',
        '.webp', '.pdf', '.mp4', '.webm'
    ]
    
    def filter(self, record):
        """
        Retorna False para bloquear logs de archivos estáticos.
        Retorna True para permitir el log.
        """
        # Si no hay mensaje, permitir
        if not hasattr(record, 'msg') or not isinstance(record.msg, str):
            return True
        
        msg = record.msg.lower()
        
        # Filtrar logs de archivos estáticos por path
        if any(ignored_path in msg for ignored_path in self.IGNORED_PATHS):
            return False
        
        # Filtrar por extensión de archivo
        if any(ext in msg for ext in self.STATIC_EXTENSIONS):
            return False
        
        # Filtrar GETs exitosos (200, 304) - Solo logear errores y mutaciones
        if '"get ' in msg and (' 200 ' in msg or ' 304 ' in msg):
            # Permitir solo ciertos GETs importantes
            important_gets = ['/admin/', '/api/', '/dashboard']
            if not any(path in msg for path in important_gets):
                return False
        
        # Filtrar favicon requests independientemente del método
        if 'favicon' in msg:
            return False
        
        return True


class OnlyErrorsFilter(logging.Filter):
    """
    Filtro que solo permite logs de nivel ERROR o superior.
    Útil para producción cuando solo quieres ver problemas.
    """
    
    def filter(self, record):
        return record.levelno >= logging.ERROR


class SensitiveDataFilter(logging.Filter):
    """
    Filtro que remueve datos sensibles de logs (passwords, tokens, CSRF)
    pero MANTIENE emails visibles para trazabilidad y monitoreo interno.
    
    IMPORTANTE: Este filtro NO anonimiza emails porque son necesarios para:
    - Trazabilidad de acciones de usuarios
    - Debugging y soporte
    - Monitoreo de seguridad (login attempts, etc)
    
    Si necesitas cumplir con GDPR, configura exportación de logs a Sentry
    y usa anonimización en esa capa externa.
    """
    
    SENSITIVE_PATTERNS = [
        # Tokens CSRF
        (r'csrfmiddlewaretoken=[A-Za-z0-9]{64}', 'csrfmiddlewaretoken=[FILTERED]'),
        # Passwords en URLs/forms
        (r'password=[^&\s]*', 'password=[FILTERED]'),
        # API Keys
        (r'api_key=[^&\s]*', 'api_key=[FILTERED]'),
        # Tokens de sesión
        (r'sessionid=[^&\s]*', 'sessionid=[FILTERED]'),
        # Authorization headers
        (r'Authorization:\s*Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Authorization: Bearer [FILTERED]'),
    ]
    
    def filter(self, record):
        """
        Remueve datos sensibles del registro de log, pero mantiene emails
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            cleaned_msg = record.msg
            
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                cleaned_msg = re.sub(pattern, replacement, cleaned_msg, flags=re.IGNORECASE)
            
            record.msg = cleaned_msg
        
        # También limpiar args si existen
        if hasattr(record, 'args') and record.args:
            cleaned_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    cleaned_arg = arg
                    for pattern, replacement in self.SENSITIVE_PATTERNS:
                        cleaned_arg = re.sub(pattern, replacement, cleaned_arg, flags=re.IGNORECASE)
                    cleaned_args.append(cleaned_arg)
                else:
                    cleaned_args.append(arg)
            record.args = tuple(cleaned_args)
        
        return True
