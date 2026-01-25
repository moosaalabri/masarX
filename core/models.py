from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Country(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

class Governate(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name=_('Country'))
    name = models.CharField(_('Name'), max_length=100)
    
    def __str__(self):
        return f"{self.name} ({self.country.name})"

    class Meta:
        verbose_name = _('Governate')
        verbose_name_plural = _('Governates')

class City(models.Model):
    governate = models.ForeignKey(Governate, on_delete=models.CASCADE, verbose_name=_('Governate'))
    name = models.CharField(_('Name'), max_length=100)
    
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
    
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Country'))
    governate = models.ForeignKey(Governate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Governate'))
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('City'))

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

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
