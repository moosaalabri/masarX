import os
import time
from .models import Profile, PlatformProfile

def project_context(request):
    """
    Adds project-specific environment variables to the template context globally.
    """
    profile = None
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except:
            profile, created = Profile.objects.get_or_create(user=request.user)
    
    platform_profile = PlatformProfile.objects.first()
            
    return {
        "project_description": os.getenv("PROJECT_DESCRIPTION", ""),
        "project_image_url": os.getenv("PROJECT_IMAGE_URL", ""),
        # Used for cache-busting static assets
        "deployment_timestamp": int(time.time()),
        "user_profile": profile,
        "platform_profile": platform_profile,
    }