import os
from django import template

register = template.Library()


@register.filter
def filename(value):
    return os.path.basename(value)

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)
