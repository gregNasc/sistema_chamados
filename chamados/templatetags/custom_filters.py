from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retorna o valor de um dict ou QueryDict"""
    if hasattr(dictionary, 'getlist'):
        return dictionary.getlist(key)
    return dictionary.get(key, [])