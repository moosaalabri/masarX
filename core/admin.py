from django.contrib import admin
from .models import Profile, Parcel, Country, Governate, City, PlatformProfile

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_ar')
    search_fields = ('name_en', 'name_ar')

@admin.register(Governate)
class GovernateAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_ar', 'country')
    list_filter = ('country',)
    search_fields = ('name_en', 'name_ar')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_ar', 'governate')
    list_filter = ('governate__country', 'governate')
    search_fields = ('name_en', 'name_ar')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'country', 'governate', 'city')
    list_filter = ('role', 'country', 'governate')
    search_fields = ('user__username', 'phone_number')

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'shipper', 'carrier', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'pickup_country', 'delivery_country')
    search_fields = ('tracking_number', 'shipper__username', 'carrier__username', 'receiver_name')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')

@admin.register(PlatformProfile)
class PlatformProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'registration_number')
    fieldsets = (
        (None, {
            'fields': ('name', 'logo', 'slogan')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone_number', 'registration_number', 'vat_number')
        }),
        ('Legal', {
            'fields': ('privacy_policy', 'terms_conditions')
        }),
        ('WhatsApp Configuration', {
            'fields': ('whatsapp_access_token', 'whatsapp_business_phone_number_id'),
            'description': 'Enter your Meta WhatsApp Business API credentials here. These will override the system defaults.'
        }),
    )
    
    def has_add_permission(self, request):
        # Allow adding only if no instance exists
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)