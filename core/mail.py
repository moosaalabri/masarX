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
    
    Args:
        name (str): Sender's name
        email (str): Sender's email
        message (str): The message content
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        subject = f"New Contact Message from {name}"
        full_message = f"You have received a new message from your website contact form.\n\n" \
                       f"Name: {name}\n" \
                       f"Email: {email}\n\n" \
                       f"Message:\n{message}"
        
        recipient_list = settings.CONTACT_EMAIL_TO or [settings.DEFAULT_FROM_EMAIL]
        
        # Use HTML email for contact form too, for consistency
        return send_html_email(
            subject=subject,
            message=full_message,
            recipient_list=recipient_list,
            title="New Contact Message"
        )
    except Exception as e:
        logger.error(f"Failed to send contact message: {e}")
        return False