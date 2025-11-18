"""
Middleware de Validación de Sesión para prevenir Session Hijacking.

Este middleware valida que la sesión no haya sido comprometida verificando
el User-Agent del navegador.

Si se detecta un cambio en el User-Agent, la sesión se invalida
y se fuerza al usuario a autenticarse nuevamente.
"""

import logging
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class SessionValidationMiddleware:
    """
    Middleware que previene Session Hijacking validando User-Agent.
    
    Configuración en settings.py:
    - SESSION_VALIDATE_USER_AGENT: bool (default: True)
    - SESSION_VALIDATION_EXEMPTS: list - rutas exentas de validación
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuración
        self.validate_user_agent = getattr(
            settings, 
            'SESSION_VALIDATE_USER_AGENT', 
            True
        )
        self.exempt_urls = getattr(
            settings, 
            'SESSION_VALIDATION_EXEMPTS', 
            ['/login/', '/logout/', '/password_reset/', '/admin/']
        )
        
    def __call__(self, request):
        # Si el usuario no está autenticado, no validar
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Verificar si la ruta está exenta
        if self._is_exempt(request.path):
            return self.get_response(request)
        
        # Obtener User-Agent actual
        current_user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Validar User-Agent
        if self.validate_user_agent:
            stored_user_agent = request.session.get('_session_user_agent')
            
            if stored_user_agent is None:
                # Primera vez, guardar User-Agent
                request.session['_session_user_agent'] = current_user_agent
            elif not self._user_agents_match(stored_user_agent, current_user_agent):
                # User-Agent cambió significativamente - posible session hijacking
                logger.warning(
                    f"SESSION HIJACKING DETECTED | User: {request.user.username} | "
                    f"Original UA: {stored_user_agent[:80]}... | "
                    f"Current UA: {current_user_agent[:80]}..."
                )
                return self._invalidate_session(request, "User-Agent cambió")
        
        response = self.get_response(request)
        return response
    
    def _is_exempt(self, path):
        """Verifica si la ruta está exenta de validación."""
        return any(path.startswith(exempt) for exempt in self.exempt_urls)
    
    def _user_agents_match(self, stored_ua, current_ua):
        """
        Compara User-Agents de forma robusta, tolerando variaciones menores.
        
        Esto previene falsos positivos con navegadores móviles (especialmente iOS)
        que pueden variar ligeramente el User-Agent entre requests.
        
        Estrategia:
        1. Si son exactamente iguales, OK
        2. Normalizar espacios y comparar
        3. Extraer componentes principales (navegador, OS) y comparar
        """
        # Comparación exacta
        if stored_ua == current_ua:
            return True
        
        # Normalizar espacios en blanco
        stored_normalized = ' '.join(stored_ua.split())
        current_normalized = ' '.join(current_ua.split())
        
        if stored_normalized == current_normalized:
            return True
        
        # Extraer componentes principales para comparación tolerante
        def extract_signature(ua):
            """
            Extrae la firma principal del User-Agent ignorando versiones menores.
            Ejemplo: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)"
            """
            import re
            
            # Extraer plataforma principal (iPhone, Windows, Mac, etc.)
            platform_match = re.search(r'\((.*?)\)', ua)
            platform = platform_match.group(1) if platform_match else ''
            
            # Simplificar plataforma eliminando versiones específicas
            # "iPhone; CPU iPhone OS 18_7" -> "iPhone; CPU iPhone OS"
            platform = re.sub(r'\d+[_\.]\d+', '', platform)
            
            # Extraer nombre del navegador (Safari, Chrome, Firefox, etc.)
            browser_match = re.search(r'(Chrome|Safari|Firefox|Edge|Opera)[\/\s]', ua)
            browser = browser_match.group(1) if browser_match else ''
            
            return f"{platform}|{browser}".lower()
        
        stored_signature = extract_signature(stored_ua)
        current_signature = extract_signature(current_ua)
        
        # Si las firmas principales coinciden, considerar como match
        if stored_signature == current_signature:
            return True
        
        # Si llegamos aquí, los User-Agents son significativamente diferentes
        return False
    
    def _invalidate_session(self, request, reason):
        """Invalida la sesión y redirige al login."""
        username = request.user.username
        
        # Log detallado para auditoría
        logger.error(
            f"SESSION INVALIDATED | User: {username} | "
            f"Reason: {reason} | "
            f"Path: {request.path} | "
            f"Method: {request.method}"
        )
        
        # Hacer logout (limpia la sesión)
        logout(request)
        
        # Mensaje para el usuario
        messages.error(
            request,
            "Tu sesión ha sido cerrada por razones de seguridad. "
            "Por favor, inicia sesión nuevamente."
        )
        
        # Redirigir al login con next para volver a la página original
        login_url = reverse('accounts:login')
        next_url = request.path
        
        return redirect(f'{login_url}?next={next_url}')


class SessionMetadataMiddleware:
    """
    Middleware auxiliar que guarda metadatos de la sesión en login.
    
    Este middleware debe ir DESPUÉS de SessionValidationMiddleware
    y se encarga de registrar información inicial de la sesión.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Si el usuario acaba de autenticarse, guardar metadatos
        if request.user.is_authenticated:
            if '_session_user_agent' not in request.session:
                # Primera autenticación, registrar metadatos
                request.session['_session_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
                request.session['_session_created_at'] = request.session.get(
                    '_session_created_at',
                    str(request.session.session_key)
                )
                
                logger.info(
                    f"SESSION METADATA REGISTERED | "
                    f"User: {request.user.username} | "
                    f"UA: {request.session.get('_session_user_agent', '')[:50]}..."
                )
        
        response = self.get_response(request)
        return response
