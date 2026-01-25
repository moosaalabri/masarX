from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid

class Profile(models.Model):
    ROLE_CHOICES = (
        ('shipper', _('Shipper')),
        ('car_owner', _('Car Owner')),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('User'))
    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES, default='shipper')
    phone_number = models.CharField(_('Phone Number'), max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

class Parcel(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending Pickup')),
        ('picked_up', _('Picked Up')),
        ('in_transit', _('In Transit')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    )
    
    tracking_number = models.CharField(_('Tracking Number'), max_length=20, unique=True, blank=True)
    shipper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_parcels', verbose_name=_('Shipper'))
    carrier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='carried_parcels', verbose_name=_('Carrier'))
    
    description = models.TextField(_('Description'))
    weight = models.DecimalField(_('Weight (kg)'), max_digits=5, decimal_places=2, help_text=_("Weight in kg"))
    
    pickup_address = models.CharField(_('Pickup Address'), max_length=255)
    delivery_address = models.CharField(_('Delivery Address'), max_length=255)
    
    receiver_name = models.CharField(_('Receiver Name'), max_length=100)
    receiver_phone = models.CharField(_('Receiver Phone'), max_length=20)
    
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
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