"""
Filtros personalizados para logging de Django
"""
import logging
import re
from urllib.parse import urlparse, parse_qs

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

class SensitiveDataFilter(logging.Filter):
    """
    Filtro que remueve datos sensibles de todos los logs
    """
    
    SENSITIVE_PATTERNS = [
        # Tokens CSRF
        (r'csrfmiddlewaretoken=[A-Za-z0-9]{64}', 'csrfmiddlewaretoken=[FILTERED]'),
        # Passwords
        (r'password=[^&\s]*', 'password=[FILTERED]'),
        # API Keys
        (r'api_key=[^&\s]*', 'api_key=[FILTERED]'),
        # Tokens de sesión
        (r'sessionid=[^&\s]*', 'sessionid=[FILTERED]'),
        # Email completos (solo mostrar primera parte)
        (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1@[DOMAIN]'),
    ]
    
    def filter(self, record):
        """
        Remueve datos sensibles del registro de log
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
