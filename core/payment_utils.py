import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ThawaniPay:
    def __init__(self):
        self.api_key = settings.THAWANI_API_KEY
        self.base_url = settings.THAWANI_API_URL
        self.headers = {
            "thawani-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_checkout_session(self, parcel, success_url, cancel_url):
        endpoint = f"{self.base_url}/checkout/session"
        
        # Thawani expects price in baiza (1 OMR = 1000 baiza)
        # We need to convert Decimal price to integer baiza
        amount_baiza = int(parcel.price * 1000)
        
        payload = {
            "client_reference_id": str(parcel.tracking_number),
            "mode": "payment",
            "products": [
                {
                    "name": f"Shipping for Parcel {parcel.tracking_number}",
                    "unit_amount": amount_baiza,
                    "quantity": 1
                }
            ],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "parcel_id": parcel.id,
                "customer_name": parcel.shipper.get_full_name() or parcel.shipper.username,
                "customer_phone": parcel.shipper.profile.phone_number
            }
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return data["data"]["session_id"]
            else:
                logger.error(f"Thawani Error: {data.get('description')}")
                return None
        except Exception as e:
            logger.error(f"Thawani Request Failed: {str(e)}")
            return None

    def get_checkout_session(self, session_id):
        endpoint = f"{self.base_url}/checkout/session/{session_id}"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return data["data"]
            return None
        except Exception as e:
            logger.error(f"Thawani Check Failed: {str(e)}")
            return None
