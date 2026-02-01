from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key - returns True/False for selected state"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, False)
    return False
