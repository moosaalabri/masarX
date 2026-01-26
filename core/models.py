from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid

class Country(models.Model):
    name_en = models.CharField(_('Name (English)'), max_length=100)
    name_ar = models.CharField(_('Name (Arabic)'), max_length=100)
    phone_code = models.CharField(_('Phone Code'), max_length=10, blank=True, help_text=_("e.g. +968"))
    
    @property
    def name(self):
        if get_language() == 'ar':
            return self.name_ar
        return self.name_en

    def __str__(self):
        return f"{self.name} ({self.phone_code})" if self.phone_code else self.name

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

class Governate(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name=_('Country'))
    name_en = models.CharField(_('Name (English)'), max_length=100)
    name_ar = models.CharField(_('Name (Arabic)'), max_length=100)
    
    @property
    def name(self):
        if get_language() == 'ar':
            return self.name_ar
        return self.name_en

    def __str__(self):
        return f"{self.name} ({self.country.name})"

    class Meta:
        verbose_name = _('Governate')
        verbose_name_plural = _('Governates')

class City(models.Model):
    governate = models.ForeignKey(Governate, on_delete=models.CASCADE, verbose_name=_('Governate'))
    name_en = models.CharField(_('Name (English)'), max_length=100)
    name_ar = models.CharField(_('Name (Arabic)'), max_length=100)
    
    @property
    def name(self):
        if get_language() == 'ar':
            return self.name_ar
        return self.name_en

    def __str__(self):
        return f"{self.name} ({self.governate.name})"

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')

class Profile(models.Model):
    ROLE_CHOICES = (
        ('shipper', _('Shipper')),
        ('car_owner', _('Car Owner')),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('User'))
    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES, default='shipper')
    phone_number = models.CharField(_('Phone Number'), max_length=20, blank=True)
    profile_picture = models.ImageField(_('Profile Picture'), upload_to='profile_pics/', blank=True, null=True)
    address = models.CharField(_('Address'), max_length=255, blank=True)
    
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Country'))
    governate = models.ForeignKey(Governate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Governate'))
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('City'))

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
        
    def get_average_rating(self):
        if self.role != 'car_owner':
            return None
        ratings = self.user.received_ratings.all()
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)

    def get_rating_count(self):
        if self.role != 'car_owner':
            return 0
        return self.user.received_ratings.count()

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Parcel(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending Pickup')),
        ('picked_up', _('Picked Up')),
        ('in_transit', _('In Transit')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
    )
    
    tracking_number = models.CharField(_('Tracking Number'), max_length=20, unique=True, blank=True)
    shipper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_parcels', verbose_name=_('Shipper'))
    carrier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='carried_parcels', verbose_name=_('Carrier'))
    
    description = models.TextField(_('Description'))
    weight = models.DecimalField(_('Weight (kg)'), max_digits=5, decimal_places=2, help_text=_("Weight in kg"))
    price = models.DecimalField(_('Price (OMR)'), max_digits=10, decimal_places=3, default=0.000)
    
    # Pickup Location
    pickup_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_parcels', verbose_name=_('Pickup Country'))
    pickup_governate = models.ForeignKey(Governate, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_parcels', verbose_name=_('Pickup Governate'))
    pickup_city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_parcels', verbose_name=_('Pickup City'))
    pickup_address = models.CharField(_('Pickup Address'), max_length=255)
    
    # Delivery Location
    delivery_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_parcels', verbose_name=_('Delivery Country'))
    delivery_governate = models.ForeignKey(Governate, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_parcels', verbose_name=_('Delivery Governate'))
    delivery_city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_city_parcels', verbose_name=_('Delivery City'))
    delivery_address = models.CharField(_('Delivery Address'), max_length=255)
    
    receiver_name = models.CharField(_('Receiver Name'), max_length=100)
    receiver_phone = models.CharField(_('Receiver Phone'), max_length=20)
    
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(_('Payment Status'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    thawani_session_id = models.CharField(_('Thawani Session ID'), max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = str(uuid.uuid4().hex[:10]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Parcel {self.tracking_number} - {self.status}"

    class Meta:
        verbose_name = _('Parcel')
        verbose_name_plural = _('Parcels')

class PlatformProfile(models.Model):
    name = models.CharField(_('Platform Name'), max_length=100)
    logo = models.ImageField(_('Logo'), upload_to='platform_logos/', blank=True, null=True)
    slogan = models.CharField(_('Slogan'), max_length=255, blank=True)
    address = models.TextField(_('Address'), blank=True)
    phone_number = models.CharField(_('Phone Number'), max_length=50, blank=True)
    registration_number = models.CharField(_('Registration Number'), max_length=100, blank=True)
    vat_number = models.CharField(_('VAT Number'), max_length=100, blank=True)
    privacy_policy = models.TextField(_('Privacy Policy'), blank=True)
    terms_conditions = models.TextField(_('Terms and Conditions'), blank=True)
    
    # WhatsApp Configuration (Wablas Gateway)
    whatsapp_access_token = models.TextField(_('Wablas API Token'), blank=True, help_text=_("Your Wablas API Token."))
    whatsapp_business_phone_number_id = models.CharField(_('Wablas Domain'), max_length=100, blank=True, default="https://deu.wablas.com", help_text=_("The Wablas API domain (e.g., https://deu.wablas.com)."))
    whatsapp_app_secret = models.CharField(_('Wablas Secret Key'), max_length=255, blank=True, help_text=_("Your Wablas API Secret Key (if required)."))

    # Payment Configuration
    enable_payment = models.BooleanField(_('Enable Payment'), default=True, help_text=_("Toggle to enable or disable payments on the platform."))

    def save(self, *args, **kwargs):
        # Auto-clean whitespace from credentials
        if self.whatsapp_access_token:
            self.whatsapp_access_token = self.whatsapp_access_token.strip()
        if self.whatsapp_business_phone_number_id:
            val = self.whatsapp_business_phone_number_id.strip()
            # Remove common path suffixes if user pasted full URL
            for suffix in ['/api/send-message', '/api/v2/send-message']:
                if val.endswith(suffix):
                    val = val[:-len(suffix)]
            if val.endswith('/'):
                val = val[:-1]
            self.whatsapp_business_phone_number_id = val
        if self.whatsapp_app_secret:
            self.whatsapp_app_secret = self.whatsapp_app_secret.strip()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Platform Profile')
        verbose_name_plural = _('Platform Profile')

class OTPVerification(models.Model):
    PURPOSE_CHOICES = (
        ('profile_update', _('Profile Update')),
        ('password_reset', _('Password Reset')),
        ('registration', _('Registration')),
        ('login', _('Login')),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='profile_update')
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # OTP valid for 10 minutes
        return self.created_at >= timezone.now() - timezone.timedelta(minutes=10)

class Testimonial(models.Model):
    name_en = models.CharField(_('Name (English)'), max_length=100)
    name_ar = models.CharField(_('Name (Arabic)'), max_length=100)
    role_en = models.CharField(_('Role (English)'), max_length=100)
    role_ar = models.CharField(_('Role (Arabic)'), max_length=100)
    content_en = models.TextField(_('Testimony (English)'))
    content_ar = models.TextField(_('Testimony (Arabic)'))
    image = models.ImageField(_('Image'), upload_to='testimonials/', blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def name(self):
        return self.name_ar if get_language() == 'ar' else self.name_en

    @property
    def role(self):
        return self.role_ar if get_language() == 'ar' else self.role_en

    @property
    def content(self):
        return self.content_ar if get_language() == 'ar' else self.content_en

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')
        ordering = ['-created_at']

class DriverRating(models.Model):
    parcel = models.OneToOneField(Parcel, on_delete=models.CASCADE, related_name='rating', verbose_name=_('Parcel'))
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings', verbose_name=_('Driver'))
    shipper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings', verbose_name=_('Shipper'))
    rating = models.PositiveSmallIntegerField(_('Rating'), choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(_('Comment'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for {self.driver.username} by {self.shipper.username}"

    class Meta:
        verbose_name = _('Driver Rating')
        verbose_name_plural = _('Driver Ratings')