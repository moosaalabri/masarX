import requests
import logging
from django.conf import settings
from .models import PlatformProfile

logger = logging.getLogger(__name__)

def get_whatsapp_credentials():
    """
    Retrieves WhatsApp credentials from PlatformProfile (preferred) or settings.
    Returns tuple: (api_key, phone_id)
    """
    # Default to settings
    api_key = settings.WHATSAPP_API_KEY
    phone_id = settings.WHATSAPP_PHONE_ID

    # Try to fetch from PlatformProfile
    try:
        profile = PlatformProfile.objects.first()
        if profile:
            if profile.whatsapp_access_token:
                api_key = profile.whatsapp_access_token
            if profile.whatsapp_business_phone_number_id:
                phone_id = profile.whatsapp_business_phone_number_id
    except Exception as e:
        logger.warning(f"Failed to fetch PlatformProfile for WhatsApp config: {e}")

    return api_key, phone_id

def send_whatsapp_message(phone_number, message):
    """
    Sends a WhatsApp message using the configured gateway.
    This implementation assumes Meta WhatsApp Business API (Graph API).
    """
    if not settings.WHATSAPP_ENABLED:
        logger.info("WhatsApp notifications are disabled by settings.")
        return False

    api_key, phone_id = get_whatsapp_credentials()

    if not api_key or not phone_id:
        logger.warning("WhatsApp API configuration is missing (checked PlatformProfile and settings).")
        return False

    # Normalize phone number (ensure it has country code and no +)
    clean_phone = "".join(filter(str.isdigit, str(phone_number)))
    
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            logger.info(f"WhatsApp message sent to {clean_phone}")
            return True
        else:
            logger.error(f"WhatsApp API error: {response.status_code} - {response_data}")
            return False
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return False

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