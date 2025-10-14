from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retorna o valor de um dict ou QueryDict"""
    if hasattr(dictionary, 'getlist'):
        return dictionary.getlist(key)
    return dictionary.get(key, [])

@register.filter
def format_duracao(value):
    if not value:
        return '-'
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}min"