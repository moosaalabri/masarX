from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Parcel, Profile, Governate, City

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'phone_number', 'address', 'profile_picture']

class GovernateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Governate
        fields = ['id', 'name_en', 'name_ar']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name_en', 'name_ar']

class ParcelSerializer(serializers.ModelSerializer):
    pickup_governate_detail = GovernateSerializer(source='pickup_governate', read_only=True)
    pickup_city_detail = CitySerializer(source='pickup_city', read_only=True)
    delivery_governate_detail = GovernateSerializer(source='delivery_governate', read_only=True)
    delivery_city_detail = CitySerializer(source='delivery_city', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pickup_google_maps_url = serializers.ReadOnlyField()
    delivery_google_maps_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Parcel
        fields = '__all__'
        read_only_fields = ['shipper', 'tracking_number', 'created_at', 'updated_at', 'thawani_session_id']

class PublicParcelSerializer(serializers.ModelSerializer):
    pickup_governate_name = serializers.CharField(source='pickup_governate.name', read_only=True)
    pickup_city_name = serializers.CharField(source='pickup_city.name', read_only=True)
    delivery_governate_name = serializers.CharField(source='delivery_governate.name', read_only=True)
    delivery_city_name = serializers.CharField(source='delivery_city.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Parcel
        fields = [
            'tracking_number', 
            'status', 
            'status_display', 
            'pickup_governate_name', 
            'pickup_city_name', 
            'delivery_governate_name', 
            'delivery_city_name',
            'updated_at',
            'description'
        ]