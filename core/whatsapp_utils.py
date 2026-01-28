import requests
import logging
import json
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from .models import PlatformProfile
from .mail import send_html_email
from .notifications import get_notification_content

logger = logging.getLogger(__name__)

def get_whatsapp_credentials():
    """
    Retrieves Wablas WhatsApp credentials from PlatformProfile.
    Returns tuple: (api_token, secret_key, domain, source_info)
    """
    # Defaults
    api_token = settings.WHATSAPP_API_KEY if hasattr(settings, 'WHATSAPP_API_KEY') else ""
    domain = "https://deu.wablas.com"
    secret_key = "" 
    source = "Settings/Env"

    # Try to fetch from PlatformProfile
    try:
        profile = PlatformProfile.objects.first()
        if profile:
            if profile.whatsapp_access_token:
                api_token = profile.whatsapp_access_token.strip()
                source = "Database (PlatformProfile)"
            
            if profile.whatsapp_app_secret:
                secret_key = profile.whatsapp_app_secret.strip()
            
            if profile.whatsapp_business_phone_number_id:
                domain = profile.whatsapp_business_phone_number_id.strip()
                if domain.endswith('/'):
                    domain = domain[:-1]
            
    except Exception as e:
        logger.warning(f"Failed to fetch PlatformProfile for WhatsApp config: {e}")

    return api_token, secret_key, domain, source

def send_whatsapp_message(phone_number, message):
    """
    Sends a WhatsApp message using the Wablas gateway.
    Returns True if successful, False otherwise.
    """
    success, _ = send_whatsapp_message_detailed(phone_number, message)
    return success

def send_whatsapp_message_detailed(phone_number, message):
    """
    Sends a WhatsApp message via Wablas API and returns detailed status.
    Returns tuple: (success: bool, response_msg: str)
    """
    if not getattr(settings, 'WHATSAPP_ENABLED', True):
        msg = "WhatsApp notifications are disabled by settings (WHATSAPP_ENABLED=False)."
        logger.info(msg)
        return False, msg

    api_token, secret_key, domain, source = get_whatsapp_credentials()

    if not api_token:
        msg = f"WhatsApp API configuration (Token) is missing. (Source: {source})"
        logger.warning(msg)
        return False, msg

    clean_phone = str(phone_number).replace('+', '').replace(' ', '')
    
    if not domain.startswith('http'):
        domain = f"https://{domain}"

    url = f"{domain}/api/send-message"
    
    auth_header = api_token
    if secret_key:
        auth_header = f"{api_token}.{secret_key}"

    headers = {
        "Authorization": auth_header,
    }
    
    data = {
        "phone": clean_phone,
        "message": message,
    }
    
    try:
        logger.info(f"Attempting to send WhatsApp message to {clean_phone} via {url}")
        response = requests.post(url, headers=headers, data=data, timeout=15)
        
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        if response.status_code == 200:
            if isinstance(response_data, dict):
                if response_data.get('status') is True:
                    logger.info(f"WhatsApp message sent to {clean_phone} via Wablas")
                    return True, f"Message sent successfully via Wablas. (Source: {source})"
                else:
                    return False, f"Wablas API Logic Error (Source: {source}): {response_data}"
            else:
                return True, f"Message sent (Raw Response). (Source: {source})"
        else:
            error_msg = f"Wablas API error (Source: {source}): {response.status_code} - {response_data}"
            logger.error(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send WhatsApp message via Wablas (Source: {source}): {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def notify_admin_alert(key, context):
    """Notifies the admin via Email and WhatsApp using a template key."""
    # 1. Get Template Content (Admin likely prefers EN, or system default?)
    # Let's force EN for admin alerts for now, or check generic language setting?
    # Usually admin alerts are in EN or the default site language.
    subject, email_body, whatsapp_body = get_notification_content(key, context, language='en')

    # Email
    try:
        if hasattr(settings, 'CONTACT_EMAIL_TO') and settings.CONTACT_EMAIL_TO:
             send_html_email(
                subject=f"Admin Alert: {subject}",
                message=email_body,
                recipient_list=settings.CONTACT_EMAIL_TO,
                title="Admin Alert"
            )
    except Exception as e:
        logger.error(f"Failed to notify admin via email: {e}")
    
    # WhatsApp
    try:
        profile = PlatformProfile.objects.first()
        if profile and profile.phone_number:
             send_whatsapp_message(profile.phone_number, f"ADMIN ALERT: {subject}\n{whatsapp_body}")
    except Exception:
        pass

def notify_shipment_created(parcel):
    shipper_name = parcel.shipper.get_full_name() or parcel.shipper.username
    context = {
        'name': shipper_name,
        'description': parcel.description,
        'tracking_number': parcel.tracking_number,
        'status': parcel.get_status_display()
    }
    
    # Render for Shipper (check user language preference? For now assume session/request unavailable so maybe default or EN, 
    # OR we need a user language profile field. The user didn't ask for user-pref language yet, just bilingual templates.
    # I'll default to EN unless I can guess.)
    # Actually, if I can't determine, EN is safe.
    # Future improvement: Add language to User Profile.
    
    subj, email_msg, wa_msg = get_notification_content('shipment_created_shipper', context)

    # WhatsApp
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, wa_msg)

    # Email
    if parcel.shipper.email:
        send_html_email(
            subject=subj,
            message=email_msg,
            recipient_list=[parcel.shipper.email],
            title=subj
        )
    return True

def notify_payment_received(parcel):
    # Shipper
    shipper_name = parcel.shipper.get_full_name() or parcel.shipper.username
    context_shipper = {
        'tracking_number': parcel.tracking_number
    }
    subj, email_msg, wa_msg = get_notification_content('payment_success_shipper', context_shipper)
    
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, wa_msg)
    
    if parcel.shipper.email:
        send_html_email(
            subject=subj,
            message=email_msg,
            recipient_list=[parcel.shipper.email],
            title=subj
        )

    # Receiver
    context_receiver = {
        'receiver_name': parcel.receiver_name,
        'shipper_name': shipper_name,
        'tracking_number': parcel.tracking_number,
        'status': parcel.get_status_display()
    }
    _, _, wa_msg_rx = get_notification_content('shipment_visible_receiver', context_receiver)
    send_whatsapp_message(parcel.receiver_phone, wa_msg_rx)

def notify_driver_assigned(parcel):
    driver_name = parcel.carrier.get_full_name() or parcel.carrier.username
    shipper_name = parcel.shipper.get_full_name() or parcel.shipper.username
    
    # Get Car Plate
    car_plate = ""
    if hasattr(parcel.carrier, 'profile'):
        car_plate = parcel.carrier.profile.car_plate_number
    
    # 1. Notify Shipper
    context_shipper = {
        'tracking_number': parcel.tracking_number,
        'driver_name': driver_name,
        'car_plate_number': car_plate,
        'status': parcel.get_status_display()
    }
    subj_s, email_s, wa_s = get_notification_content('driver_pickup_shipper', context_shipper)
    
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, wa_s)
        
    if parcel.shipper.email:
        send_html_email(subject=subj_s, message=email_s, recipient_list=[parcel.shipper.email], title=subj_s)

    # 2. Notify Receiver
    context_receiver = {
        'tracking_number': parcel.tracking_number,
        'shipper_name': shipper_name,
        'driver_name': driver_name,
        'car_plate_number': car_plate
    }
    _, _, wa_r = get_notification_content('driver_pickup_receiver', context_receiver)
    send_whatsapp_message(parcel.receiver_phone, wa_r)

    # 3. Notify Driver
    context_driver = {
        'tracking_number': parcel.tracking_number,
        'shipper_name': shipper_name,
        'pickup_address': parcel.pickup_address,
        'delivery_address': parcel.delivery_address,
        'price': parcel.price
    }
    subj_d, email_d, wa_d = get_notification_content('driver_pickup_driver', context_driver)
    
    if hasattr(parcel.carrier, 'profile') and parcel.carrier.profile.phone_number:
         send_whatsapp_message(parcel.carrier.profile.phone_number, wa_d)
    
    if parcel.carrier.email:
        send_html_email(subject=subj_d, message=email_d, recipient_list=[parcel.carrier.email], title=subj_d)

    # 4. Notify Admin
    context_admin = {
        'driver_name': driver_name,
        'car_plate_number': car_plate,
        'tracking_number': parcel.tracking_number,
        'shipper_name': shipper_name,
        'price': parcel.price
    }
    notify_admin_alert('admin_alert_driver_accept', context_admin)

def notify_status_change(parcel):
    context = {
        'tracking_number': parcel.tracking_number,
        'status': parcel.get_status_display()
    }
    subj, email_msg, wa_msg = get_notification_content('shipment_status_update', context)
    
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, wa_msg)
    
    if parcel.shipper.email:
        send_html_email(subject=subj, message=email_msg, recipient_list=[parcel.shipper.email], title=subj)

    send_whatsapp_message(parcel.receiver_phone, wa_msg)
