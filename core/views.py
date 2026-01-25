from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Parcel, Profile, Country, Governate, City
from .forms import UserRegistrationForm, ParcelForm, ContactForm
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .payment_utils import ThawaniPay
from django.conf import settings
from .whatsapp_utils import (
    notify_shipment_created, 
    notify_payment_received, 
    notify_driver_assigned, 
    notify_status_change
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
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

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