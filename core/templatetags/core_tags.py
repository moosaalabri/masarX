from django import template
from core.models import PlatformProfile

register = template.Library()

@register.simple_tag
def get_platform_profile():
    return PlatformProfile.objects.first()
