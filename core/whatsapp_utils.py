import requests
import logging
import json
from django.conf import settings
from .models import PlatformProfile

logger = logging.getLogger(__name__)

def get_whatsapp_credentials():
    """
    Retrieves Wablas WhatsApp credentials from PlatformProfile.
    Returns tuple: (api_token, secret_key, domain, source_info)
    """
    # Defaults
    api_token = settings.WHATSAPP_API_KEY if hasattr(settings, 'WHATSAPP_API_KEY') else ""
    # We repurpose Phone ID as Domain in settings if needed, or default to Wablas DEU
    domain = "https://deu.wablas.com"
    secret_key = "" # Add this to settings if you want env support, but for now mostly DB
    source = "Settings/Env"

    # Try to fetch from PlatformProfile
    try:
        profile = PlatformProfile.objects.first()
        if profile:
            # Check for token override
            if profile.whatsapp_access_token:
                api_token = profile.whatsapp_access_token.strip()
                source = "Database (PlatformProfile)"
            
            # Check for secret key override
            if profile.whatsapp_app_secret:
                secret_key = profile.whatsapp_app_secret.strip()
            
            # Check for domain override
            if profile.whatsapp_business_phone_number_id:
                domain = profile.whatsapp_business_phone_number_id.strip()
                # Ensure no trailing slash
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
    Sends a WhatsApp message via Wablas V2 API and returns detailed status.
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

    # Normalize phone number (Wablas expects international format without +, e.g. 628123...)
    # Remove all non-digits
    clean_phone = "".join(filter(str.isdigit, str(phone_number)))
    
    # Construct Authorization Header
    # Wablas V2: Authorization: {$token}.{$secret_key}
    # Some Wablas servers just need Token, but docs say Token.Secret
    auth_header = api_token
    if secret_key:
        auth_header = f"{api_token}.{secret_key}"
    
    # Endpoint V2
    url = f"{domain}/api/v2/send-message"
    
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }
    
    payload = {
        "data": [
            {
                "phone": clean_phone,
                "message": message,
                "isGroup": "false",
                "flag": "instant" # Priority
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response_data = response.json()
        
        # Wablas success usually has status: true
        if response.status_code == 200 and response_data.get('status') is not False:
            logger.info(f"WhatsApp message sent to {clean_phone} via Wablas")
            return True, f"Message sent successfully via Wablas. (Source: {source})"
        else:
            error_msg = f"Wablas API error (Source: {source}): {response.status_code} - {response_data}"
            logger.error(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send WhatsApp message via Wablas (Source: {source}): {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def notify_shipment_created(parcel):
    """Notifies the shipper that the shipment request was received."""
    shipper_name = parcel.shipper.get_full_name() or parcel.shipper.username
    message = f"""Hello {shipper_name},

Your shipment request for '{parcel.description}' has been received.
Tracking Number: {parcel.tracking_number}
Status: {parcel.get_status_display()}

Please proceed to payment to make it visible to drivers."""
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        return send_whatsapp_message(parcel.shipper.profile.phone_number, message)
    return False

def notify_payment_received(parcel):
    """Notifies the shipper and receiver about successful payment."""
    # Notify Shipper
    shipper_name = parcel.shipper.get_full_name() or parcel.shipper.username
    shipper_msg = f"""Payment successful for shipment {parcel.tracking_number}.
Your shipment is now visible to available drivers."""
    
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, shipper_msg)
    
    # Notify Receiver
    receiver_msg = f"""Hello {parcel.receiver_name},

A shipment is coming your way from {shipper_name}.
Tracking Number: {parcel.tracking_number}
Status: {parcel.get_status_display()}"""
    send_whatsapp_message(parcel.receiver_phone, receiver_msg)

def notify_driver_assigned(parcel):
    """Notifies the shipper and receiver that a driver has picked up the parcel."""
    driver_name = parcel.carrier.get_full_name() or parcel.carrier.username
    msg = f"""Shipment {parcel.tracking_number} has been picked up by {driver_name}.
Status: {parcel.get_status_display()}"""
    
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, msg)
    send_whatsapp_message(parcel.receiver_phone, msg)

def notify_status_change(parcel):
    """Notifies parties about general status updates (In Transit, Delivered)."""
    msg = f"""Update for shipment {parcel.tracking_number}:
New Status: {parcel.get_status_display()}"""
    
    if hasattr(parcel.shipper, 'profile') and parcel.shipper.profile.phone_number:
        send_whatsapp_message(parcel.shipper.profile.phone_number, msg)
    send_whatsapp_message(parcel.receiver_phone, msg)