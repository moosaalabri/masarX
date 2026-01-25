from django.contrib import admin
from .models import Profile, Parcel, Country, Governate, City

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Governate)
class GovernateAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country',)
    search_fields = ('name',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'governate')
    list_filter = ('governate__country', 'governate')
    search_fields = ('name',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'country', 'governate', 'city')
    list_filter = ('role', 'country', 'governate')
    search_fields = ('user__username', 'phone_number')

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'shipper', 'carrier', 'status', 'created_at')
    list_filter = ('status', 'pickup_country', 'delivery_country')
    search_fields = ('tracking_number', 'shipper__username', 'carrier__username', 'receiver_name')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')
