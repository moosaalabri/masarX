from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

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
        
        send_mail(
            subject=subject,
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send contact message: {e}")
        return False
