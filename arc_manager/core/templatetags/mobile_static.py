"""
Template tags optimizados para archivos estáticos en móviles iOS/Safari
Soluciona problemas de cache agresivo en Safari móvil
"""
import os
import time
from django import template
from django.templatetags.static import static
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

# Cache de versiones para evitar recalcular constantemente
_version_cache = {}

def get_file_version(file_path):
    """
    Genera una versión única para el archivo basada en su timestamp de modificación
    Esto fuerza a Safari móvil a recargar el archivo cuando cambia
    """
    if file_path in _version_cache and settings.DEBUG is False:
        return _version_cache[file_path]
    
    try:
        # Construir ruta completa del archivo
        if settings.DEBUG:
            # En desarrollo, usar STATICFILES_DIRS
            full_path = None
            for static_dir in settings.STATICFILES_DIRS:
                test_path = os.path.join(static_dir, file_path)
                if os.path.exists(test_path):
                    full_path = test_path
                    break
        else:
            # En producción, usar STATIC_ROOT
            full_path = os.path.join(settings.STATIC_ROOT, file_path)
        
        if full_path and os.path.exists(full_path):
            # Usar timestamp de modificación
            mtime = os.path.getmtime(full_path)
            version = str(int(mtime))
        else:
            # Fallback: usar timestamp actual
            version = str(int(time.time()))
        
        # Cache en producción
        if not settings.DEBUG:
            _version_cache[file_path] = version
        
        return version
    except (OSError, ValueError):
        # Fallback seguro
        return str(int(time.time()))

@register.simple_tag
def mobile_static(path):
    """
    Versión optimizada de {% static %} para móviles iOS
    Agrega cache busting automático y headers específicos para Safari
    
    Uso:
    {% load mobile_static %}
    {% mobile_static 'css/base.css' %}
    """
    base_url = static(path)
    version = get_file_version(path)
    
    # Agregar parámetro de versión para cache busting
    separator = '&' if '?' in base_url else '?'
    return f"{base_url}{separator}v={version}&mobile=1"

@register.simple_tag
def mobile_css(path, media='all'):
    """
    Genera un tag <link> completo optimizado para móviles iOS
    Incluye atributos específicos para mejorar la carga en Safari móvil
    
    Uso:
    {% mobile_css 'css/base.css' %}
    {% mobile_css 'css/mobile.css' 'screen and (max-width: 768px)' %}
    """
    static_url = mobile_static(path)
    
    # Atributos específicos para Safari móvil
    attrs = [
        f'href="{static_url}"',
        'rel="stylesheet"',
        f'media="{media}"',
        'type="text/css"',
        # Preload hint para Safari móvil
        'data-optimized="ios"'
    ]
    
    return mark_safe(f'<link {" ".join(attrs)}>')

@register.simple_tag
def mobile_js(path, defer=True):
    """
    Genera un tag <script> optimizado para móviles iOS
    
    Uso:
    {% mobile_js 'js/base.js' %}
    {% mobile_js 'js/critical.js' False %}  {# Sin defer #}
    """
    static_url = mobile_static(path)
    
    attrs = [
        f'src="{static_url}"',
        'type="text/javascript"',
        'data-optimized="ios"'
    ]
    
    if defer:
        attrs.append('defer')
    
    return mark_safe(f'<script {" ".join(attrs)}></script>')

@register.simple_tag
def preload_css(path):
    """
    Genera preload link para CSS crítico en móviles
    Mejora la velocidad de carga en Safari móvil
    
    Uso:
    {% preload_css 'css/critical.css' %}
    """
    static_url = mobile_static(path)
    
    attrs = [
        f'href="{static_url}"',
        'rel="preload"',
        'as="style"',
        'type="text/css"',
        'data-critical="true"'
    ]
    
    return mark_safe(f'<link {" ".join(attrs)}>')

@register.inclusion_tag('mobile_static/critical_css.html')
def critical_css_block():
    """
    Bloque de CSS crítico para carga inmediata en móviles
    """
    return {
        'debug': settings.DEBUG,
        'critical_styles': [
            'css/base.css',
            'css/navbar.css', 
            'css/sidebar.css'
        ]
    }
