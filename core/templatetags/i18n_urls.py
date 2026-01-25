from django import template
from django.urls import translate_url as django_translate_url

register = template.Library()

@register.simple_tag(takes_context=True)
def translate_url(context, lang_code):
    request = context.get('request')
    if not request:
        return ''
    path = request.get_full_path()
    return django_translate_url(path, lang_code)
