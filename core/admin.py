from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, Parcel, Country, Governate, City, PlatformProfile, Testimonial, DriverRating, NotificationTemplate
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.shortcuts import render
from django.utils.html import format_html
from django.contrib import messages
from .whatsapp_utils import send_whatsapp_message_detailed
from django.conf import settings
from .mail import send_html_email
import logging
import csv
from django.http import HttpResponse, HttpResponseRedirect
from rangefilter.filters import DateRangeFilter
from django.template.loader import render_to_string
import weasyprint

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _('Profiles')
    fieldsets = (
        (None, {'fields': ('role', 'is_approved', 'phone_number', 'profile_picture', 'address')}),
        (_('Driver Info'), {'fields': ('license_front_image', 'license_back_image', 'car_plate_number'), 'classes': ('collapse',)}),
        (_('Location'), {'fields': ('country', 'governate', 'city'), 'classes': ('collapse',)}),
    )

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'get_role', 'get_approval_status', 'is_active', 'is_staff', 'send_whatsapp_link')
    list_filter = ('is_active', 'is_staff', 'profile__role', 'profile__is_approved')

    def get_role(self, obj):
        return obj.profile.get_role_display()
    get_role.short_description = _('Role')

    def get_approval_status(self, obj):
        return obj.profile.is_approved
    get_approval_status.short_description = _('Approved')
    get_approval_status.boolean = True

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/send-whatsapp/', self.admin_site.admin_view(self.send_whatsapp_view), name='user-send-whatsapp'),
        ]
        return custom_urls + urls

    def send_whatsapp_view(self, request, user_id):
        user = self.get_object(request, user_id)
        if not user:
            messages.error(request, _("User not found."))
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

        if not hasattr(user, 'profile') or not user.profile.phone_number:
            messages.warning(request, _("This user does not have a phone number in their profile."))
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
            
        if request.method == 'POST':
            message = request.POST.get('message')
            if message:
                success, msg = send_whatsapp_message_detailed(user.profile.phone_number, message)
                if success:
                    messages.success(request, _("WhatsApp message sent successfully."))
                    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
                else:
                    messages.error(request, _(f"Failed to send message: {msg}"))
            else:
                 messages.warning(request, _("Message cannot be empty."))

        context = dict(
           self.admin_site.each_context(request),
           user_obj=user,
           phone_number=user.profile.phone_number,
        )
        return render(request, "admin/core/user/send_whatsapp_message.html", context)

    def send_whatsapp_link(self, obj):
        if hasattr(obj, 'profile') and obj.profile.phone_number:
            return format_html(
                '<a class="button" href="{}">{}</a>',
                reverse('admin:user-send-whatsapp', args=[obj.pk]),
                _('Send WhatsApp')
            )
        return "-"
    send_whatsapp_link.short_description = _("WhatsApp")
    send_whatsapp_link.allow_tags = True

class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'shipper', 'carrier', 'price', 'status', 'payment_status', 'created_at')
    list_filter = (
        'status', 
        'payment_status', 
        ('created_at', DateRangeFilter),
    )
    search_fields = ('tracking_number', 'shipper__username', 'receiver_name', 'carrier__username')
    actions = ['export_as_csv', 'print_parcels', 'export_pdf']

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

    def print_parcels(self, request, queryset):
        return render(request, 'admin/core/parcel/parcel_list_print.html', {'parcels': queryset, 'is_pdf': False})
    print_parcels.short_description = _("Print Selected Parcels")

    def export_pdf(self, request, queryset):
        html_string = render_to_string('admin/core/parcel/parcel_list_print.html', {'parcels': queryset, 'is_pdf': True})
        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        result = html.write_pdf()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="parcels_list.pdf"'
        response.write(result)
        return response
    export_pdf.short_description = _("Download Selected as PDF")

class PlatformProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('General Info'), {
            'fields': ('name', 'logo', 'slogan', 'address', 'phone_number', 'registration_number', 'vat_number')
        }),
        (_('Policies'), {
            'fields': ('privacy_policy_en', 'privacy_policy_ar', 'terms_conditions_en', 'terms_conditions_ar')
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

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_ar', 'phone_code')
    search_fields = ('name_en', 'name_ar', 'phone_code')

class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'role_en', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name_en', 'name_ar', 'content_en', 'content_ar')
    list_editable = ('is_active',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Governate)
admin.site.register(City)
admin.site.register(PlatformProfile, PlatformProfileAdmin)
admin.site.register(Testimonial, TestimonialAdmin)
admin.site.register(DriverRating)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('key', 'description')
    readonly_fields = ('key', 'description', 'available_variables')
    search_fields = ('key', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('key', 'description', 'available_variables')
        }),
        (_('Email Content'), {
            'fields': ('subject_en', 'subject_ar', 'email_body_en', 'email_body_ar'),
            'description': _('For emails, the body is wrapped in a base template. Use HTML if needed.')
        }),
        (_('WhatsApp Content'), {
            'fields': ('whatsapp_body_en', 'whatsapp_body_ar'),
            'description': _('For WhatsApp, use plain text with newlines.')
        }),
    )

    def has_add_permission(self, request):
        return False # Prevent adding new keys manually
        
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(NotificationTemplate, NotificationTemplateAdmin)