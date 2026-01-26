from django import template
from core.models import PlatformProfile, DriverRating

register = template.Library()

@register.simple_tag
def get_platform_profile():
    return PlatformProfile.objects.first()

@register.simple_tag
def get_rating(parcel):
    try:
        return parcel.rating
    except:
        return None