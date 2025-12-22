from django import template

register = template.Library()

@register.filter(name='lookup')
def lookup(dictionary, key):
    """
    Permet d'accéder aux valeurs d'un dictionnaire avec une clé dynamique
    Usage: {{ dictionary|lookup:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
