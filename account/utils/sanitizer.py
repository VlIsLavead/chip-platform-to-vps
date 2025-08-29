from html_sanitizer import Sanitizer

sanitizer = Sanitizer({
    'tags': {'b', 'i', 'span', 'br', 'div', 'p'},
    'attributes': {'span': ('style',)},
    'empty': {'br'},
    'separate': {'div', 'p'},
    'whitespace': {'br'},
})