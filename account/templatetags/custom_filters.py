import os
import re
from django import template

register = template.Library()


@register.filter
def filename(value):
    return os.path.basename(value)


@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)


@register.filter
def clean_filename(value):
    """
    Очищает имя файла от случайного суффикса Django
    Например: 'test_E3qhwb2.txt' -> 'test.txt'
              'document_abc123.pdf' -> 'document.pdf'
              'файл_AbC123.docx' -> 'файл.docx'
    """
    if not value:
        return ''
    
    filename = os.path.basename(value)
    
    if '.' in filename:
        name_parts = filename.rsplit('.', 1)
        name = name_parts[0]
        extension = '.' + name_parts[1]
        
        clean_name = re.sub(r'_[A-Za-z0-9]{6,8}$', '', name)
        
        if clean_name:
            return clean_name + extension
        else:
            return filename
    else:
        return re.sub(r'_[A-Za-z0-9]{6,8}$', '', filename)


@register.filter
def endswith(value, arg):
    """
    Проверяет, заканчивается ли строка на arg
    Используется для проверки расширений файлов
    """
    return str(value).lower().endswith(str(arg).lower())