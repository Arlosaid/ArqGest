from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key, [])
    except Exception:
        return []


@register.filter(name='dict_get')
def dict_get(value, key):
    """Obtiene value[key] si es un dict; de lo contrario retorna None."""
    try:
        if isinstance(value, dict):
            return value.get(key)
        return None
    except Exception:
        return None

