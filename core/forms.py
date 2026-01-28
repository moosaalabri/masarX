from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from .models import Profile, Parcel, Country, Governate, City, DriverRating

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label=_("Name"), widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Your Name')}))
    email = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Your Email')}))
    subject = forms.CharField(max_length=200, label=_("Subject"), widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Subject')}))
    message = forms.CharField(label=_("Message"), widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': _('Your Message')}))

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password_confirm = forms.CharField(widget=forms.PasswordInput, label=_("Confirm Password"))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label=_("Register as"))
    
    phone_code = forms.ModelChoiceField(queryset=Country.objects.none(), label=_("Code"), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, label=_("Phone Number"))
    
    verification_method = forms.ChoiceField(choices=[('email', _('Email')), ('whatsapp', _('WhatsApp'))], label=_("Verify via"), widget=forms.RadioSelect, initial='email')
    
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
        lang = get_language()
        name_field = 'name_ar' if lang == 'ar' else 'name_en'
        
        # Phone Code setup
        self.fields['phone_code'].queryset = Country.objects.exclude(phone_code='').order_by(name_field)
        self.fields['phone_code'].label_from_instance = lambda obj: f"{obj.phone_code} ({obj.name})"
        
        self.fields['country'].queryset = Country.objects.all().order_by(name_field)
        
        # Default Country logic
        oman = Country.objects.filter(name_en='Oman').first()
        if oman:
            self.fields['country'].initial = oman
            self.fields['phone_code'].initial = oman
        
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['governate'].queryset = Governate.objects.filter(country_id=country_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and hasattr(self.instance, 'profile') and self.instance.profile.country:
            self.fields['governate'].queryset = self.instance.profile.country.governate_set.order_by(name_field)
        elif oman:
            self.fields['governate'].queryset = Governate.objects.filter(country=oman).order_by(name_field)

        if 'governate' in self.data:
            try:
                governate_id = int(self.data.get('governate'))
                self.fields['city'].queryset = City.objects.filter(governate_id=governate_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and hasattr(self.instance, 'profile') and self.instance.profile.governate:
            self.fields['city'].queryset = self.instance.profile.governate.city_set.order_by(name_field)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_("Passwords don't match"))
        return password_confirm

    def clean(self):
        cleaned_data = super().clean()
        phone_code = cleaned_data.get('phone_code')
        phone_number = cleaned_data.get('phone_number')
        
        if phone_code and phone_number:
            # If user didn't type the code in the phone number input, prepend it
            if not phone_number.startswith(phone_code.phone_code):
                 cleaned_data['phone_number'] = f"{phone_code.phone_code}{phone_number}"
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Profile is created by signal, so we update it
            profile, created = Profile.objects.get_or_create(user=user)
            # Handle role if it exists in cleaned_data (it might be excluded in subclasses)
            if 'role' in self.cleaned_data:
                profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.country = self.cleaned_data['country']
            profile.governate = self.cleaned_data['governate']
            profile.city = self.cleaned_data['city']
            
            # Save extra driver fields if they exist
            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                profile.profile_picture = self.cleaned_data['profile_picture']
            if 'license_front_image' in self.cleaned_data and self.cleaned_data['license_front_image']:
                profile.license_front_image = self.cleaned_data['license_front_image']
            if 'license_back_image' in self.cleaned_data and self.cleaned_data['license_back_image']:
                profile.license_back_image = self.cleaned_data['license_back_image']
            if 'car_plate_number' in self.cleaned_data:
                profile.car_plate_number = self.cleaned_data['car_plate_number']
                
            profile.save()
        return user

class ShipperRegistrationForm(UserRegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget = forms.HiddenInput()
        self.fields['role'].initial = 'shipper'

class DriverRegistrationForm(UserRegistrationForm):
    profile_picture = forms.ImageField(label=_("Profile Picture (Webcam/Upload)"), required=True, widget=forms.FileInput(attrs={'class': 'form-control', 'capture': 'user', 'accept': 'image/*'}))
    license_front_image = forms.ImageField(label=_("License Front Image"), required=True, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    license_back_image = forms.ImageField(label=_("License Back Image"), required=True, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    car_plate_number = forms.CharField(label=_("Car Plate Number"), max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget = forms.HiddenInput()
        self.fields['role'].initial = 'car_owner'

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label=_("First Name"), max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label=_("Last Name"), max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    phone_code = forms.ModelChoiceField(queryset=Country.objects.none(), label=_("Code"), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label=_("Phone Number"), max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    address = forms.CharField(label=_("Address"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(label=_("Profile Picture"), required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    otp_method = forms.ChoiceField(
        choices=[('email', _('Email')), ('whatsapp', _('WhatsApp'))], 
        label=_('Verify changes via'), 
        widget=forms.RadioSelect,
        initial='email'
    )

    class Meta:
        model = Profile
        fields = ['profile_picture', 'phone_number', 'address', 'country', 'governate', 'city']
        widgets = {
             'country': forms.Select(attrs={'class': 'form-control'}),
             'governate': forms.Select(attrs={'class': 'form-control'}),
             'city': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'country': _('Country'),
            'governate': _('Governate'),
            'city': _('City'),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            
        lang = get_language()
        name_field = 'name_ar' if lang == 'ar' else 'name_en'
        
        # Phone Code setup
        self.fields['phone_code'].queryset = Country.objects.exclude(phone_code='').order_by(name_field)
        self.fields['phone_code'].label_from_instance = lambda obj: f"{obj.phone_code} ({obj.name})"
        
        # Default Country logic (Oman)
        oman = Country.objects.filter(name_en='Oman').first()
        if oman:
             self.fields['phone_code'].initial = oman

        # Initial splitting of phone number
        if self.instance.pk and self.instance.phone_number:
            for country in Country.objects.exclude(phone_code=''):
                if self.instance.phone_number.startswith(country.phone_code):
                    self.fields['phone_code'].initial = country
                    # Strip code from display
                    self.fields['phone_number'].initial = self.instance.phone_number[len(country.phone_code):]
                    break
        
        self.fields['country'].queryset = Country.objects.all().order_by(name_field)
        
        # Initial QS setup
        self.fields['governate'].queryset = Governate.objects.none()
        self.fields['city'].queryset = City.objects.none()

        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['governate'].queryset = Governate.objects.filter(country_id=country_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.country:
             self.fields['governate'].queryset = self.instance.country.governate_set.order_by(name_field)
        elif oman:
             self.fields['governate'].queryset = Governate.objects.filter(country=oman).order_by(name_field)

        if 'governate' in self.data:
            try:
                gov_id = int(self.data.get('governate'))
                self.fields['city'].queryset = City.objects.filter(governate_id=gov_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.governate:
             self.fields['city'].queryset = self.instance.governate.city_set.order_by(name_field)

    def clean(self):
        cleaned_data = super().clean()
        phone_code = cleaned_data.get('phone_code')
        phone_number = cleaned_data.get('phone_number')
        
        if phone_code and phone_number:
            if not phone_number.startswith(phone_code.phone_code):
                 cleaned_data['phone_number'] = f"{phone_code.phone_code}{phone_number}"
        return cleaned_data

class ParcelForm(forms.ModelForm):
    receiver_phone_code = forms.ModelChoiceField(queryset=Country.objects.none(), label=_("Receiver Code"), required=False, widget=forms.Select(attrs={'class': 'form-control'}))

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
            'price': _('Your Offer Price (Bid) (OMR)'),
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
        lang = get_language()
        name_field = 'name_ar' if lang == 'ar' else 'name_en'

        # Phone Code setup
        self.fields['receiver_phone_code'].queryset = Country.objects.exclude(phone_code='').order_by(name_field)
        self.fields['receiver_phone_code'].label_from_instance = lambda obj: f"{obj.phone_code} ({obj.name})"
        
        # Default Country logic (Oman) - Only if not editing
        oman = Country.objects.filter(name_en='Oman').first()
        if not self.instance.pk and oman:
            self.fields['receiver_phone_code'].initial = oman
            self.fields['pickup_country'].initial = oman
            self.fields['delivery_country'].initial = oman

        # Initial splitting of phone number (if editing)
        if self.instance.pk and self.instance.receiver_phone:
            for country in Country.objects.exclude(phone_code=''):
                if self.instance.receiver_phone.startswith(country.phone_code):
                    self.fields['receiver_phone_code'].initial = country
                    self.fields['receiver_phone'].initial = self.instance.receiver_phone[len(country.phone_code):]
                    break

        # Set querysets for countries
        self.fields['pickup_country'].queryset = Country.objects.all().order_by(name_field)
        self.fields['delivery_country'].queryset = Country.objects.all().order_by(name_field)
        
        # Pickup
        self.fields['pickup_governate'].queryset = Governate.objects.none()
        self.fields['pickup_city'].queryset = City.objects.none()

        if 'pickup_country' in self.data:
            try:
                country_id = int(self.data.get('pickup_country'))
                self.fields['pickup_governate'].queryset = Governate.objects.filter(country_id=country_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.pickup_country:
             self.fields['pickup_governate'].queryset = Governate.objects.filter(country=self.instance.pickup_country).order_by(name_field)
        elif oman:
            self.fields['pickup_governate'].queryset = Governate.objects.filter(country=oman).order_by(name_field)
        
        if 'pickup_governate' in self.data:
            try:
                gov_id = int(self.data.get('pickup_governate'))
                self.fields['pickup_city'].queryset = City.objects.filter(governate_id=gov_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.pickup_governate:
             self.fields['pickup_city'].queryset = City.objects.filter(governate_id=self.instance.pickup_governate.id).order_by(name_field)

        # Delivery
        self.fields['delivery_governate'].queryset = Governate.objects.none()
        self.fields['delivery_city'].queryset = City.objects.none()

        if 'delivery_country' in self.data:
            try:
                country_id = int(self.data.get('delivery_country'))
                self.fields['delivery_governate'].queryset = Governate.objects.filter(country_id=country_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.delivery_country:
             self.fields['delivery_governate'].queryset = Governate.objects.filter(country=self.instance.delivery_country).order_by(name_field)
        elif oman:
            self.fields['delivery_governate'].queryset = Governate.objects.filter(country=oman).order_by(name_field)
        
        if 'delivery_governate' in self.data:
            try:
                gov_id = int(self.data.get('delivery_governate'))
                self.fields['delivery_city'].queryset = City.objects.filter(governate_id=gov_id).order_by(name_field)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.delivery_governate:
             self.fields['delivery_city'].queryset = City.objects.filter(governate_id=self.instance.delivery_governate.id).order_by(name_field)

    def clean(self):
        cleaned_data = super().clean()
        phone_code = cleaned_data.get('receiver_phone_code')
        phone_number = cleaned_data.get('receiver_phone')
        
        if phone_code and phone_number:
            if not phone_number.startswith(phone_code.phone_code):
                 cleaned_data['receiver_phone'] = f"{phone_code.phone_code}{phone_number}"
        return cleaned_data

class DriverRatingForm(forms.ModelForm):
    class Meta:
        model = DriverRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-stars'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Write your review here...')}),
        }
        labels = {
            'rating': _('Rating'),
            'comment': _('Comment'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reverse choices for CSS star rating logic (5 to 1) to ensure left-to-right filling
        self.fields['rating'].choices = [(i, str(i)) for i in range(5, 0, -1)]
