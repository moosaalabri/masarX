from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_html_email(subject, message, recipient_list, title=None, action_url=None, action_text=None, request=None):
    """
    Sends a styled HTML email using the platform template.
    """
    try:
        from .models import PlatformProfile
        platform = PlatformProfile.objects.first()
        if not platform:
            # Create a dummy platform object if none exists, to avoid errors
            class DummyPlatform:
                name = "Platform"
                logo = None
                address = ""
            platform = DummyPlatform()
            
        # Determine site URL
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        if request:
            site_url = f"{request.scheme}://{request.get_host()}"
            
        context = {
            'platform': platform,
            'title': title or subject,
            'message': message,
            'action_url': action_url,
            'action_text': action_text,
            'site_url': site_url,
        }
        
        html_content = render_to_string('emails/base_email.html', context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        logger.error(f"Failed to send HTML email: {e}")
        # Fallback to plain text
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            return True
        except Exception as e2:
            logger.error(f"Failed to send fallback email: {e2}")
            return False

def send_contact_message(name, email, message):
    """
    Sends a contact form message to the platform admins.
    """
    try:
        from .notifications import get_notification_content
        
        context = {'name': name, 'email': email, 'message': message}
        # Admin alerts default to EN
        subj, email_msg, wa_msg = get_notification_content('contact_form_admin', context, language='en')
        
        recipient_list = settings.CONTACT_EMAIL_TO or [settings.DEFAULT_FROM_EMAIL]
        
        # Email
        email_sent = send_html_email(
            subject=subj,
            message=email_msg,
            recipient_list=recipient_list,
            title="New Contact Message"
        )
        
        # WhatsApp (New feature: Notify admin on WhatsApp too)
        try:
            from .models import PlatformProfile
            from .whatsapp_utils import send_whatsapp_message
            
            profile = PlatformProfile.objects.first()
            if profile and profile.phone_number:
                send_whatsapp_message(profile.phone_number, wa_msg)
        except Exception as e:
            logger.warning(f"Failed to send admin WhatsApp for contact form: {e}")
            
        return email_sent
    except Exception as e:
        logger.error(f"Failed to send contact message: {e}")
        return False
