from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Profile, Parcel

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password_confirm = forms.CharField(widget=forms.PasswordInput, label=_("Confirm Password"))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label=_("Register as"))
    phone_number = forms.CharField(max_length=20, label=_("Phone Number"))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': _('Username'),
            'email': _('Email'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
        }

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
            Profile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone_number=self.cleaned_data['phone_number']
            )
        return user

class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = ['description', 'weight', 'pickup_address', 'delivery_address', 'receiver_name', 'receiver_phone']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('What are you sending?')}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'pickup_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('123 Street, City')}),
            'delivery_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('456 Avenue, City')}),
            'receiver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'description': _('Package Description'),
            'weight': _('Weight (kg)'),
            'pickup_address': _('Pickup Address'),
            'delivery_address': _('Delivery Address'),
            'receiver_name': _('Receiver Name'),
            'receiver_phone': _('Receiver Phone'),
        }
