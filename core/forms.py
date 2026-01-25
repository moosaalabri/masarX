from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Profile, Parcel, Country, Governate, City

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password_confirm = forms.CharField(widget=forms.PasswordInput, label=_("Confirm Password"))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label=_("Register as"))
    phone_number = forms.CharField(max_length=20, label=_("Phone Number"))
    
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=False, label=_("Country"))
    governate = forms.ModelChoiceField(queryset=Governate.objects.none(), required=False, label=_("Governate"))
    city = forms.ModelChoiceField(queryset=City.objects.none(), required=False, label=_("City"))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': _('Username'),
            'email': _('Email'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['governate'].queryset = Governate.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and hasattr(self.instance, 'profile') and self.instance.profile.country:
            self.fields['governate'].queryset = self.instance.profile.country.governate_set.order_by('name')

        if 'governate' in self.data:
            try:
                governate_id = int(self.data.get('governate'))
                self.fields['city'].queryset = City.objects.filter(governate_id=governate_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and hasattr(self.instance, 'profile') and self.instance.profile.governate:
            self.fields['city'].queryset = self.instance.profile.governate.city_set.order_by('name')

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_("Passwords don't match"))
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Profile is created by signal, so we update it
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.country = self.cleaned_data['country']
            profile.governate = self.cleaned_data['governate']
            profile.city = self.cleaned_data['city']
            profile.save()
        return user

class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = [
            'description', 'weight', 'price',
            'pickup_country', 'pickup_governate', 'pickup_city', 'pickup_address', 
            'delivery_country', 'delivery_governate', 'delivery_city', 'delivery_address', 
            'receiver_name', 'receiver_phone'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('What are you sending?')}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            
            'pickup_country': forms.Select(attrs={'class': 'form-control'}),
            'pickup_governate': forms.Select(attrs={'class': 'form-control'}),
            'pickup_city': forms.Select(attrs={'class': 'form-control'}),
            'pickup_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Street/Building')}),
            
            'delivery_country': forms.Select(attrs={'class': 'form-control'}),
            'delivery_governate': forms.Select(attrs={'class': 'form-control'}),
            'delivery_city': forms.Select(attrs={'class': 'form-control'}),
            'delivery_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Street/Building')}),
            
            'receiver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'description': _('Package Description'),
            'weight': _('Weight (kg)'),
            'price': _('Shipping Price (OMR)'),
            'pickup_country': _('Pickup Country'),
            'pickup_governate': _('Pickup Governate'),
            'pickup_city': _('Pickup City'),
            'pickup_address': _('Pickup Address (Street/Building)'),
            'delivery_country': _('Delivery Country'),
            'delivery_governate': _('Delivery Governate'),
            'delivery_city': _('Delivery City'),
            'delivery_address': _('Delivery Address (Street/Building)'),
            'receiver_name': _('Receiver Name'),
            'receiver_phone': _('Receiver Phone'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pickup
        self.fields['pickup_governate'].queryset = Governate.objects.none()
        self.fields['pickup_city'].queryset = City.objects.none()

        if 'pickup_country' in self.data:
            try:
                country_id = int(self.data.get('pickup_country'))
                self.fields['pickup_governate'].queryset = Governate.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass
        
        if 'pickup_governate' in self.data:
            try:
                gov_id = int(self.data.get('pickup_governate'))
                self.fields['pickup_city'].queryset = City.objects.filter(governate_id=gov_id).order_by('name')
            except (ValueError, TypeError):
                pass

        # Delivery
        self.fields['delivery_governate'].queryset = Governate.objects.none()
        self.fields['delivery_city'].queryset = City.objects.none()

        if 'delivery_country' in self.data:
            try:
                country_id = int(self.data.get('delivery_country'))
                self.fields['delivery_governate'].queryset = Governate.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass
        
        if 'delivery_governate' in self.data:
            try:
                gov_id = int(self.data.get('delivery_governate'))
                self.fields['delivery_city'].queryset = City.objects.filter(governate_id=gov_id).order_by('name')
            except (ValueError, TypeError):
                pass