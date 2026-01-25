from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Parcel, Profile, Country, Governate, City
from .forms import UserRegistrationForm, ParcelForm
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse

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
        available_parcels = Parcel.objects.filter(status='pending').order_by('-created_at')
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
        
    parcel = get_object_or_404(Parcel, id=parcel_id, status='pending')
    parcel.carrier = request.user
    parcel.status = 'picked_up'
    parcel.save()
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
            messages.success(request, _("Status updated successfully!"))
    return redirect('dashboard')

def article_detail(request):
    return render(request, 'core/article_detail.html')

def get_governates(request):
    country_id = request.GET.get('country_id')
    governates = Governate.objects.filter(country_id=country_id).values('id', 'name')
    return JsonResponse(list(governates), safe=False)

def get_cities(request):
    governate_id = request.GET.get('governate_id')
    cities = City.objects.filter(governate_id=governate_id).values('id', 'name')
    return JsonResponse(list(cities), safe=False)
