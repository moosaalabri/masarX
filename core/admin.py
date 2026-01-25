from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, Parcel, Country, Governate, City, PlatformProfile, Testimonial
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.shortcuts import render
from django.utils.html import format_html
from django.contrib import messages
from .whatsapp_utils import send_whatsapp_message_detailed
from django.core.mail import send_mail
from django.conf import settings
from .mail import send_html_email
import logging
import csv
from django.http import HttpResponse

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _('Profiles')

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'shipper', 'carrier', 'price', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('tracking_number', 'shipper__username', 'receiver_name', 'carrier__username')
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="parcels_report.csv"'
        writer = csv.writer(response)

        writer.writerow(['Tracking Number', 'Shipper', 'Carrier', 'Price (OMR)', 'Status', 'Payment Status', 'Created At', 'Updated At'])
        
        for obj in queryset:
            writer.writerow([
                obj.tracking_number,
                obj.shipper.username if obj.shipper else '',
                obj.carrier.username if obj.carrier else '',
                obj.price,
                obj.get_status_display(),
                obj.get_payment_status_display(),
                obj.created_at,
                obj.updated_at
            ])

        return response
    export_as_csv.short_description = _("Export Selected to CSV")

class PlatformProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('General Info'), {
            'fields': ('name', 'logo', 'slogan', 'address', 'phone_number', 'registration_number', 'vat_number')
        }),
        (_('Policies'), {
            'fields': ('privacy_policy', 'terms_conditions')
        }),
        (_('Payment Configuration'), {
            'fields': ('enable_payment',)
        }),
        (_('WhatsApp Configuration (Wablas Gateway)'), {
            'fields': ('whatsapp_access_token', 'whatsapp_app_secret', 'whatsapp_business_phone_number_id'),
            'description': _('Configure your Wablas API connection. Use "Test WhatsApp Configuration" to verify.')
        }),
    )
    
    def has_add_permission(self, request):
        # Allow only one instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('test-whatsapp/', self.admin_site.admin_view(self.test_whatsapp_view), name='test-whatsapp'),
            path('test-email/', self.admin_site.admin_view(self.test_email_view), name='test-email'),
        ]
        return custom_urls + urls

    def test_whatsapp_view(self, request):
        phone_number = ''
        if request.method == 'POST':
            phone_number = request.POST.get('phone_number')
            if phone_number:
                success, msg = send_whatsapp_message_detailed(phone_number, "This is a test message from your Platform.")
                if success:
                    messages.success(request, f"Success: {msg}")
                else:
                    messages.error(request, f"Error: {msg}")
            else:
                messages.warning(request, "Please enter a phone number.")
        
        context = dict(
           self.admin_site.each_context(request),
           phone_number=phone_number,
        )
        return render(request, "admin/core/platformprofile/test_whatsapp.html", context)

    def test_email_view(self, request):
        email = ''
        if request.method == 'POST':
            email = request.POST.get('email')
            if email:
                try:
                    send_html_email(
                        subject="Test Email from Platform",
                        message="This is a test email to verify your platform's email configuration. If you see the logo and nice formatting, it works!",
                        recipient_list=[email],
                        title="Test Email",
                        request=request
                    )
                    messages.success(request, f"Success: Test email sent to {email}.")
                except Exception as e:
                    messages.error(request, f"Error sending email: {str(e)}")
            else:
                messages.warning(request, "Please enter an email address.")
        
        context = dict(
           self.admin_site.each_context(request),
           email=email,
        )
        return render(request, "admin/core/platformprofile/test_email.html", context)

    def test_connection_link(self, obj):
        return format_html(
            '<a class="button" href="{}" style="margin-right: 10px;">{}</a>'
            '<a class="button" href="{}">{}</a>',
            reverse('admin:test-whatsapp'),
            _('Test WhatsApp'),
            reverse('admin:test-email'),
            _('Test Email')
        )
    test_connection_link.short_description = _("Actions")
    test_connection_link.allow_tags = True
    
    readonly_fields = ('test_connection_link',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Add the test link to the first fieldset or a new one
        if obj:
             # Check if 'Tools' fieldset already exists to avoid duplication if called multiple times (though get_fieldsets is usually fresh)
             # Easier: just append it.
             fieldsets += ((_('Tools'), {'fields': ('test_connection_link',)}),)
        return fieldsets

class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'role_en', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name_en', 'name_ar', 'content_en', 'content_ar')
    list_editable = ('is_active',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Country)
admin.site.register(Governate)
admin.site.register(City)
admin.site.register(PlatformProfile, PlatformProfileAdmin)
admin.site.register(Testimonial, TestimonialAdmin)