from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Parcel, Profile, Country, Governate, City, OTPVerification, PlatformProfile
from .forms import UserRegistrationForm, ParcelForm, ContactForm, UserProfileForm
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .payment_utils import ThawaniPay
from django.conf import settings
from django.core.mail import send_mail
import random
import string
from .whatsapp_utils import (
    notify_shipment_created, 
    notify_payment_received, 
    notify_driver_assigned, 
    notify_status_change,
    send_whatsapp_message
)
from .mail import send_contact_message

def index(request):
    tracking_id = request.GET.get('tracking_id')
    parcel = None
    error = None
    if tracking_id:
        try:
            parcel = Parcel.objects.get(tracking_number=tracking_id)
        except Parcel.DoesNotExist:
            error = _("Parcel not found.")
    
    return render(request, 'core/index.html', {
        'parcel': parcel,
        'error': error,
        'tracking_id': tracking_id
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save user but inactive
            user = form.save(commit=True)
            user.is_active = False
            user.save()

            # Generate OTP
            code = ''.join(random.choices(string.digits, k=6))
            OTPVerification.objects.create(user=user, code=code, purpose='registration')

            # Send OTP
            method = form.cleaned_data.get('verification_method', 'email')
            if method == 'whatsapp':
                phone = user.profile.phone_number
                send_whatsapp_message(phone, f"Your verification code is: {code}")
                messages.info(request, _("Verification code sent to WhatsApp."))
            else:
                send_mail(
                    _('Verification Code'),
                    f'Your verification code is: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.info(request, _("Verification code sent to email."))

            request.session['registration_user_id'] = user.id
            return redirect('verify_registration')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def verify_registration(request):
    if 'registration_user_id' not in request.session:
        messages.error(request, _("Session expired or invalid."))
        return redirect('register')

    if request.method == 'POST':
        code = request.POST.get('code')
        user_id = request.session['registration_user_id']
        try:
            user = User.objects.get(id=user_id)
            otp = OTPVerification.objects.filter(
                user=user, 
                code=code, 
                purpose='registration', 
                is_verified=False
            ).latest('created_at')
            
            if otp.is_valid():
                # Activate User
                user.is_active = True
                user.save()
                
                # Cleanup
                otp.is_verified = True
                otp.save()
                del request.session['registration_user_id']
                
                # Login
                login(request, user)
                
                messages.success(request, _("Account verified successfully!"))
                return redirect('dashboard')
            else:
                messages.error(request, _("Invalid or expired code."))
        except (User.DoesNotExist, OTPVerification.DoesNotExist):
            messages.error(request, _("Invalid code."))
            
    return render(request, 'core/verify_registration.html')

@login_required
def dashboard(request):
    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if profile.role == 'shipper':
        parcels = Parcel.objects.filter(shipper=request.user).order_by('-created_at')
        return render(request, 'core/shipper_dashboard.html', {'parcels': parcels})
    else:
        # Car Owner view
        available_parcels = Parcel.objects.filter(status='pending', payment_status='paid').order_by('-created_at')
        my_parcels = Parcel.objects.filter(carrier=request.user).exclude(status='delivered').order_by('-created_at')
        return render(request, 'core/driver_dashboard.html', {
            'available_parcels': available_parcels,
            'my_parcels': my_parcels
        })

@login_required
def shipment_request(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.role != 'shipper':
        messages.error(request, _("Only shippers can request shipments."))
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ParcelForm(request.POST)
        if form.is_valid():
            parcel = form.save(commit=False)
            parcel.shipper = request.user
            parcel.save()
            
            # WhatsApp Notification
            notify_shipment_created(parcel)
            
            messages.success(request, _("Shipment requested successfully! Tracking ID: ") + parcel.tracking_number)
            return redirect('dashboard')
    else:
        form = ParcelForm()
    return render(request, 'core/shipment_request.html', {'form': form})

@login_required
def accept_parcel(request, parcel_id):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.role != 'car_owner':
        messages.error(request, _("Only car owners can accept shipments."))
        return redirect('dashboard')
        
    parcel = get_object_or_404(Parcel, id=parcel_id, status='pending', payment_status='paid')
    parcel.carrier = request.user
    parcel.status = 'picked_up'
    parcel.save()
    
    # WhatsApp Notification
    notify_driver_assigned(parcel)
    
    messages.success(request, _("You have accepted the shipment!"))
    return redirect('dashboard')

@login_required
def update_status(request, parcel_id):
    parcel = get_object_or_404(Parcel, id=parcel_id, carrier=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Parcel.STATUS_CHOICES):
            parcel.status = new_status
            parcel.save()
            
            # WhatsApp Notification
            notify_status_change(parcel)
            
            messages.success(request, _("Status updated successfully!"))
    return redirect('dashboard')

@login_required
def initiate_payment(request, parcel_id):
    # Check if payments are enabled
    platform_profile = PlatformProfile.objects.first()
    if platform_profile and not platform_profile.enable_payment:
        messages.error(request, _("Payments are currently disabled by the administrator."))
        return redirect('dashboard')

    parcel = get_object_or_404(Parcel, id=parcel_id, shipper=request.user, payment_status='pending')
    
    thawani = ThawaniPay()
    success_url = request.build_absolute_uri(reverse('payment_success')) + f"?session_id={{CHECKOUT_SESSION_ID}}&parcel_id={parcel.id}"
    cancel_url = request.build_absolute_uri(reverse('payment_cancel')) + f"?parcel_id={parcel.id}"
    
    session_id = thawani.create_checkout_session(parcel, success_url, cancel_url)
    
    if session_id:
        parcel.thawani_session_id = session_id
        parcel.save()
        checkout_url = f"{settings.THAWANI_API_URL.replace('/api/v1', '')}/pay/{session_id}?key={settings.THAWANI_PUBLISHABLE_KEY}"
        return redirect(checkout_url)
    else:
        messages.error(request, _("Could not initiate payment. Please try again later."))
        return redirect('dashboard')

@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    parcel_id = request.GET.get('parcel_id')
    parcel = get_object_or_404(Parcel, id=parcel_id, shipper=request.user)
    
    thawani = ThawaniPay()
    session_data = thawani.get_checkout_session(session_id)
    
    if session_data and session_data.get('payment_status') == 'paid':
        parcel.payment_status = 'paid'
        parcel.save()
        
        # WhatsApp Notification
        notify_payment_received(parcel)
        
        messages.success(request, _("Payment successful! Your shipment is now active."))
    else:
        messages.warning(request, _("Payment status is pending or failed. Please check your dashboard."))
        
    return redirect('dashboard')

@login_required
def payment_cancel(request):
    messages.info(request, _("Payment was cancelled."))
    return redirect('dashboard')

def article_detail(request):
    return render(request, 'core/article_detail.html')

def get_governates(request):
    country_id = request.GET.get('country_id')
    lang = get_language()
    field_name = 'name_ar' if lang == 'ar' else 'name_en'
    governates = Governate.objects.filter(country_id=country_id).order_by(field_name)
    data = [{'id': g.id, 'name': getattr(g, field_name)} for g in governates]
    return JsonResponse(data, safe=False)

def get_cities(request):
    governate_id = request.GET.get('governate_id')
    lang = get_language()
    field_name = 'name_ar' if lang == 'ar' else 'name_en'
    cities = City.objects.filter(governate_id=governate_id).order_by(field_name)
    data = [{'id': c.id, 'name': getattr(c, field_name)} for c in cities]
    return JsonResponse(data, safe=False)

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def terms_conditions(request):
    return render(request, 'core/terms_conditions.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email
            sent = send_contact_message(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )
            if sent:
                messages.success(request, _("Your message has been sent successfully!"))
            else:
                messages.error(request, _("There was an error sending your message. Please try again later."))
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'core/profile.html', {'profile': request.user.profile})

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            # 1. Handle Image immediately (easier than session storage)
            if 'profile_picture' in request.FILES:
                request.user.profile.profile_picture = request.FILES['profile_picture']
                request.user.profile.save()

            # 2. Store other data in session for verification
            data = form.cleaned_data
            # Remove objects that can't be serialized or we've already handled
            safe_data = {
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email'],
                'phone_number': data['phone_number'],
                'address': data['address'],
                'country_id': data['country'].id if data['country'] else None,
                'governate_id': data['governate'].id if data['governate'] else None,
                'city_id': data['city'].id if data['city'] else None,
            }
            request.session['pending_profile_update'] = safe_data
            
            # 3. Generate OTP
            code = ''.join(random.choices(string.digits, k=6))
            OTPVerification.objects.create(user=request.user, code=code, purpose='profile_update')
            
            # 4. Send OTP
            method = data.get('otp_method', 'email')
            if method == 'whatsapp':
                # Use current phone if available, else new phone
                phone = request.user.profile.phone_number or data['phone_number']
                send_whatsapp_message(phone, f"Your verification code is: {code}")
                messages.info(request, _("Verification code sent to WhatsApp."))
            else:
                # Default to email
                # Send to the NEW email address (from the form), not the old one
                target_email = data['email']
                send_mail(
                    _('Verification Code'),
                    f'Your verification code is: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [target_email],
                    fail_silently=False,
                )
                messages.info(request, _("Verification code sent to email."))
            
            return redirect('verify_otp')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'core/edit_profile.html', {'form': form})

@login_required
def verify_otp_view(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            otp = OTPVerification.objects.filter(
                user=request.user, 
                code=code, 
                purpose='profile_update', 
                is_verified=False
            ).latest('created_at')
            
            if otp.is_valid():
                # Apply changes
                data = request.session.get('pending_profile_update')
                if data:
                    # Update User
                    request.user.first_name = data['first_name']
                    request.user.last_name = data['last_name']
                    request.user.email = data['email']
                    request.user.save()
                    
                    # Update Profile
                    profile = request.user.profile
                    profile.phone_number = data['phone_number']
                    profile.address = data['address']
                    if data.get('country_id'):
                        profile.country_id = data['country_id']
                    if data.get('governate_id'):
                        profile.governate_id = data['governate_id']
                    if data.get('city_id'):
                        profile.city_id = data['city_id']
                    profile.save()
                    
                    # Cleanup
                    otp.is_verified = True
                    otp.save()
                    del request.session['pending_profile_update']
                    
                    messages.success(request, _("Profile updated successfully!"))
                    return redirect('profile')
                else:
                    messages.error(request, _("Session expired. Please try again."))
                    return redirect('edit_profile')
            else:
                messages.error(request, _("Invalid or expired code."))
        except OTPVerification.DoesNotExist:
            messages.error(request, _("Invalid code."))
            
    return render(request, 'core/verify_otp.html')