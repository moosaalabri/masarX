from django.contrib import admin
from .models import Profile, Parcel

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number')
    list_filter = ('role',)
    search_fields = ('user__username', 'phone_number')

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'shipper', 'carrier', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('tracking_number', 'receiver_name', 'receiver_phone')
    readonly_fields = ('tracking_number',)