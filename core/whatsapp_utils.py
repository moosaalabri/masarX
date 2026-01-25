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
    secret_key = "" 
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

    # Normalize phone number (Wablas expects international format without +, e.g. 628123...)
    clean_phone = str(phone_number).replace('+', '').replace(' ', '')
    
    # Endpoint: /api/send-message (Simple Text)
    # Ensure domain has schema
    if not domain.startswith('http'):
        domain = f"https://{domain}"

    # Using the exact endpoint provided in user example
    url = f"{domain}/api/send-message"
    
    # Header construction logic from user example
    auth_header = api_token
    if secret_key:
        auth_header = f"{api_token}.{secret_key}"

    headers = {
        "Authorization": auth_header,
        # requests will set Content-Type to application/x-www-form-urlencoded when using 'data' param
    }
    
    # Payload as form data (not JSON)
    data = {
        "phone": clean_phone,
        "message": message,
    }
    
    # Note: User's example didn't add 'secret' to payload, only to header.
    # We will stick to user's example strictly.

    try:
        # Use data=data for form-urlencoded
        response = requests.post(url, headers=headers, data=data, timeout=15)
        
        # Handle non-JSON response (HTML error pages)
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        # Wablas success usually has status: true
        if response.status_code == 200:
            # Check for logical success in JSON
            if isinstance(response_data, dict):
                if response_data.get('status') is True:
                    logger.info(f"WhatsApp message sent to {clean_phone} via Wablas")
                    return True, f"Message sent successfully via Wablas. (Source: {source})"
                else:
                    return False, f"Wablas API Logic Error (Source: {source}): {response_data}"
            else:
                # If text, assume success if 200 OK? Or inspect text.
                return True, f"Message sent (Raw Response). (Source: {source})"
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