from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Parcel, Profile
from .forms import UserRegistrationForm
from django.utils.translation import gettext_lazy as _

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
            return redirect('index')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def shipment_request(request):
    if request.method == 'POST':
        # Logic for creating shipment will go here
        pass
    return render(request, 'core/shipment_request.html')

def article_detail(request):
    return render(request, 'core/article_detail.html')
