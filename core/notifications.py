from django.utils.translation import get_language
from .models import NotificationTemplate
from django.template import Template, Context
import logging

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = {
    'otp_registration': {
        'description': 'Sent when a user registers (Email/WhatsApp)',
        'variables': '{{ code }}',
        'subject_en': 'Verification Code',
        'subject_ar': 'رمز التحقق',
        'email_body_en': 'Your Masar Verification Code is {{ code }}',
        'email_body_ar': 'رمز التحقق الخاص بك هو {{ code }}',
        'whatsapp_body_en': 'Your Masar Verification Code is {{ code }}',
        'whatsapp_body_ar': 'رمز التحقق الخاص بك هو {{ code }}',
    },
    'otp_login': {
        'description': 'Sent for 2FA Login (Email/WhatsApp)',
        'variables': '{{ code }}',
        'subject_en': 'Login OTP',
        'subject_ar': 'رمز الدخول',
        'email_body_en': 'Your Masar Login Code is {{ code }}. Do not share this code.',
        'email_body_ar': 'رمز دخول مسار هو {{ code }}. لا تشارك هذا الرمز.',
        'whatsapp_body_en': 'Your Masar Login Code is {{ code }}. Do not share this code.',
        'whatsapp_body_ar': 'رمز دخول مسار هو {{ code }}. لا تشارك هذا الرمز.',
    },
    'otp_profile_update': {
        'description': 'Sent when updating profile sensitive info',
        'variables': '{{ code }}',
        'subject_en': 'Verification Code',
        'subject_ar': 'رمز التحقق',
        'email_body_en': 'Your Masar Update Code is {{ code }}',
        'email_body_ar': 'رمز التحديث الخاص بك هو {{ code }}',
        'whatsapp_body_en': 'Your Masar Update Code is {{ code }}',
        'whatsapp_body_ar': 'رمز التحديث الخاص بك هو {{ code }}',
    },
    'shipment_created_shipper': {
        'description': 'Sent to Shipper when they create a shipment',
        'variables': '{{ name }}, {{ description }}, {{ tracking_number }}, {{ status }}, {{ distance }}, {{ price }}',
        'subject_en': 'Shipment Request Received - {{ tracking_number }}',
        'subject_ar': 'تم استلام طلب الشحنة - {{ tracking_number }}',
        'email_body_en': "Hello {{ name }},\n\nYour shipment request for '{{ description }}' has been received.\nTracking Number: {{ tracking_number }}\nDistance: {{ distance }} km\nPrice: {{ price }} OMR\nStatus: {{ status }}\n\nPlease proceed to payment to make it visible to drivers.",
        'email_body_ar': "مرحباً {{ name }}،\n\nتم استلام طلب الشحنة '{{ description }}'.\nرقم التتبع: {{ tracking_number }}\nالمسافة: {{ distance }} كم\nالسعر: {{ price }} ر.ع\nالحالة: {{ status }}\n\nيرجى متابعة الدفع لجعلها مرئية للسائقين.",
        'whatsapp_body_en': "Hello {{ name }}\nYour shipment request for '{{ description }}' has been received.\nTracking Number: {{ tracking_number }}\nDistance: {{ distance }} km\nPrice: {{ price }} OMR\nStatus: {{ status }}\nPlease proceed to payment.",
        'whatsapp_body_ar': "مرحباً {{ name }}،\nتم استلام طلب الشحنة '{{ description }}'.\nرقم التتبع: {{ tracking_number }}\nالمسافة: {{ distance }} كم\nالسعر: {{ price }} ر.ع\nالحالة: {{ status }}\nيرجى الدفع.",
    },
    'payment_success_shipper': {
        'description': 'Sent to Shipper after payment',
        'variables': '{{ tracking_number }}',
        'subject_en': 'Payment Successful - {{ tracking_number }}',
        'subject_ar': 'تم الدفع بنجاح - {{ tracking_number }}',
        'email_body_en': 'Payment successful for shipment {{ tracking_number }}.\nYour shipment is now visible to available drivers.',
        'email_body_ar': 'تم الدفع بنجاح للشحنة {{ tracking_number }}.\nشحنتك الآن مرئية للسائقين المتاحين.',
        'whatsapp_body_en': 'Payment successful for shipment {{ tracking_number }}.\nYour shipment is now visible to available drivers.',
        'whatsapp_body_ar': 'تم الدفع بنجاح للشحنة {{ tracking_number }}.\nشحنتك الآن مرئية للسائقين المتاحين.',
    },
    'shipment_visible_receiver': {
        'description': 'Sent to Receiver when shipment is paid/ready',
        'variables': '{{ receiver_name }}, {{ shipper_name }}, {{ tracking_number }}, {{ status }}',
        'subject_en': 'Incoming Shipment - {{ tracking_number }}',
        'subject_ar': 'شحنة واردة - {{ tracking_number }}',
        'email_body_en': 'Hello {{ receiver_name }},\n\nA shipment is coming your way from {{ shipper_name }}.\nTracking Number: {{ tracking_number }}\nStatus: {{ status }}',
        'email_body_ar': 'مرحباً {{ receiver_name }}،\n\nشحنة قادمة إليك من {{ shipper_name }}.\nرقم التتبع: {{ tracking_number }}\nالحالة: {{ status }}',
        'whatsapp_body_en': 'Hello {{ receiver_name }},\nA shipment is coming your way from {{ shipper_name }}.\nTracking Number: {{ tracking_number }}\nStatus: {{ status }}',
        'whatsapp_body_ar': 'مرحباً {{ receiver_name }}،\nشحنة قادمة إليك من {{ shipper_name }}.\nرقم التتبع: {{ tracking_number }}\nالحالة: {{ status }}',
    },
    'driver_pickup_shipper': {
        'description': 'Sent to Shipper when driver picks up',
        'variables': '{{ tracking_number }}, {{ driver_name }}, {{ car_plate_number }}, {{ status }}',
        'subject_en': 'Driver Assigned - {{ tracking_number }}',
        'subject_ar': 'تم تعيين سائق - {{ tracking_number }}',
        'email_body_en': 'Shipment {{ tracking_number }} has been picked up by {{ driver_name }}.\nCar Plate: {{ car_plate_number }}\nStatus: {{ status }}',
        'email_body_ar': 'الشحنة {{ tracking_number }} تم استلامها بواسطة {{ driver_name }}.\nرقم اللوحة: {{ car_plate_number }}\nالحالة: {{ status }}',
        'whatsapp_body_en': 'Shipment {{ tracking_number }} has been picked up by {{ driver_name }}.\nCar Plate: {{ car_plate_number }}\nStatus: {{ status }}',
        'whatsapp_body_ar': 'الشحنة {{ tracking_number }} تم استلامها بواسطة {{ driver_name }}.\nرقم اللوحة: {{ car_plate_number }}\nالحالة: {{ status }}',
    },
    'driver_pickup_receiver': {
        'description': 'Sent to Receiver when driver picks up',
        'variables': '{{ tracking_number }}, {{ shipper_name }}, {{ driver_name }}, {{ car_plate_number }}',
        'subject_en': 'Shipment On The Way - {{ tracking_number }}',
        'subject_ar': 'الشحنة في الطريق - {{ tracking_number }}',
        'email_body_en': 'Shipment {{ tracking_number }} from {{ shipper_name }} is on the way (Picked up).\nDriver: {{ driver_name }}\nCar Plate: {{ car_plate_number }}',
        'email_body_ar': 'الشحنة {{ tracking_number }} من {{ shipper_name }} في الطريق (تم الاستلام).\nالسائق: {{ driver_name }}\nرقم اللوحة: {{ car_plate_number }}',
        'whatsapp_body_en': 'Shipment {{ tracking_number }} from {{ shipper_name }} is on the way (Picked up).\nDriver: {{ driver_name }}\nCar Plate: {{ car_plate_number }}',
        'whatsapp_body_ar': 'الشحنة {{ tracking_number }} من {{ shipper_name }} في الطريق (تم الاستلام).\nالسائق: {{ driver_name }}\nرقم اللوحة: {{ car_plate_number }}',
    },
    'driver_pickup_driver': {
        'description': 'Sent to Driver upon acceptance',
        'variables': '{{ tracking_number }}, {{ shipper_name }}, {{ pickup_address }}, {{ delivery_address }}, {{ price }}, {{ distance }}',
        'subject_en': 'Shipment Accepted - {{ tracking_number }}',
        'subject_ar': 'تم قبول الشحنة - {{ tracking_number }}',
        'email_body_en': 'You have successfully accepted Shipment {{ tracking_number }}.\nShipper: {{ shipper_name }}\nPickup: {{ pickup_address }}\nDelivery: {{ delivery_address }}\nDistance: {{ distance }} km\nPrice: {{ price }} OMR',
        'email_body_ar': 'لقد قبلت الشحنة {{ tracking_number }} بنجاح.\nالشاحن: {{ shipper_name }}\nالاستلام: {{ pickup_address }}\nالتوصيل: {{ delivery_address }}\nالمسافة: {{ distance }} كم\nالسعر: {{ price }} ر.ع',
        'whatsapp_body_en': 'You have successfully accepted Shipment {{ tracking_number }}.\nShipper: {{ shipper_name }}\nPickup: {{ pickup_address }}\nDelivery: {{ delivery_address }}\nDistance: {{ distance }} km\nPrice/Bid: {{ price }} OMR',
        'whatsapp_body_ar': 'لقد قبلت الشحنة {{ tracking_number }} بنجاح.\nالشاحن: {{ shipper_name }}\nالاستلام: {{ pickup_address }}\nالتوصيل: {{ delivery_address }}\nالمسافة: {{ distance }} كم\nالسعر: {{ price }} ر.ع',
    },
    'shipment_status_update': {
        'description': 'Sent on general status change (In Transit, Delivered)',
        'variables': '{{ tracking_number }}, {{ status }}',
        'subject_en': 'Shipment Update - {{ tracking_number }}',
        'subject_ar': 'تحديث الشحنة - {{ tracking_number }}',
        'email_body_en': 'Update for shipment {{ tracking_number }}:\nNew Status: {{ status }}',
        'email_body_ar': 'تحديث للشحنة {{ tracking_number }}:\nالحالة الجديدة: {{ status }}',
        'whatsapp_body_en': 'Update for shipment {{ tracking_number }}:\nNew Status: {{ status }}',
        'whatsapp_body_ar': 'تحديث للشحنة {{ tracking_number }}:\nالحالة الجديدة: {{ status }}',
    },
    'admin_alert_driver_accept': {
        'description': 'Sent to Admin when driver accepts shipment',
        'variables': '{{ driver_name }}, {{ car_plate_number }}, {{ tracking_number }}, {{ shipper_name }}, {{ price }}, {{ distance }}',
        'subject_en': 'Shipment Accepted ({{ tracking_number }})',
        'subject_ar': 'تم قبول الشحنة ({{ tracking_number }})',
        'email_body_en': 'Driver {{ driver_name }} ({{ car_plate_number }}) accepted shipment {{ tracking_number }} from {{ shipper_name }}.\nDistance: {{ distance }} km\nPrice: {{ price }} OMR',
        'email_body_ar': 'قام السائق {{ driver_name }} ({{ car_plate_number }}) بقبول الشحنة {{ tracking_number }} من {{ shipper_name }}.\nالمسافة: {{ distance }} كم\nالسعر: {{ price }} ر.ع',
        'whatsapp_body_en': 'Driver {{ driver_name }} ({{ car_plate_number }}) accepted shipment {{ tracking_number }} from {{ shipper_name }}.\nDistance: {{ distance }} km\nPrice: {{ price }} OMR',
        'whatsapp_body_ar': 'قام السائق {{ driver_name }} ({{ car_plate_number }}) بقبول الشحنة {{ tracking_number }} من {{ shipper_name }}.\nالمسافة: {{ distance }} كم\nالسعر: {{ price }} ر.ع',
    },
    'contact_form_admin': {
        'description': 'Sent to Admin when contact form is submitted',
        'variables': '{{ name }}, {{ email }}, {{ message }}',
        'subject_en': 'New Contact Message from {{ name }}',
        'subject_ar': 'رسالة جديدة من {{ name }}',
        'email_body_en': 'You have received a new message from your website contact form.\n\nName: {{ name }}\nEmail: {{ email }}\n\nMessage:\n{{ message }}',
        'email_body_ar': 'لقد تلقيت رسالة جديدة من نموذج الاتصال.\n\nالاسم: {{ name }}\nالبريد: {{ email }}\n\nالرسالة:\n{{ message }}',
        'whatsapp_body_en': 'New Message from {{ name }}:\n{{ message }}',
        'whatsapp_body_ar': 'رسالة جديدة من {{ name }}:\n{{ message }}',
    }
}

def get_notification_content(key, context, language=None):
    if not language:
        language = get_language() or 'en'
    
    # 1. Fetch or Create Template
    try:
        template_obj = NotificationTemplate.objects.get(key=key)
    except NotificationTemplate.DoesNotExist:
        # Create default
        default = DEFAULT_TEMPLATES.get(key)
        if default:
            template_obj = NotificationTemplate.objects.create(
                key=key,
                description=default.get('description', ''),
                available_variables=default.get('variables', ''),
                subject_en=default.get('subject_en', ''),
                subject_ar=default.get('subject_ar', ''),
                email_body_en=default.get('email_body_en', ''),
                email_body_ar=default.get('email_body_ar', ''),
                whatsapp_body_en=default.get('whatsapp_body_en', ''),
                whatsapp_body_ar=default.get('whatsapp_body_ar', ''),
            )
        else:
            # Fallback if key unknown
            return f"[{key}] Subject", f"[{key}] Body", f"[{key}] WA"

    # 2. Select Language Fields
    # Note: If translation is missing, fallback to EN
    if language == 'ar':
        subject = template_obj.subject_ar or template_obj.subject_en
        email_body = template_obj.email_body_ar or template_obj.email_body_en
        whatsapp_body = template_obj.whatsapp_body_ar or template_obj.whatsapp_body_en
    else:
        subject = template_obj.subject_en
        email_body = template_obj.email_body_en
        whatsapp_body = template_obj.whatsapp_body_en

    # 3. Render
    # Use Django Template engine for variable substitution
    
    def render(text, ctx):
        if not text: return ""
        try:
            # Convert context to dict if it isn't already
            if not isinstance(ctx, dict):
                ctx = {}
            t = Template(text)
            return t.render(Context(ctx))
        except Exception as e:
            logger.error(f"Template rendering error for {key}: {e}")
            return text 

    return render(subject, context), render(email_body, context), render(whatsapp_body, context)