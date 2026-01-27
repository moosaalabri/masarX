from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.db.models import Q
from .models import Parcel, Profile
from .serializers import ParcelSerializer, ProfileSerializer, PublicParcelSerializer

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Ensure profile exists
        profile, created = Profile.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'role': profile.role,
            'username': user.username
        })

class ParcelListCreateView(generics.ListCreateAPIView):
    serializer_class = ParcelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = user.profile
        
        if profile.role == 'shipper':
            return Parcel.objects.filter(shipper=user).order_by('-created_at')
        elif profile.role == 'car_owner':
            # Drivers see available parcels (pending) or their own assignments
            return Parcel.objects.filter(
                Q(status='pending') | Q(carrier=user)
            ).order_by('-created_at')
        else:
            return Parcel.objects.none()

    def perform_create(self, serializer):
        # Only shippers can create
        if self.request.user.profile.role != 'shipper':
             raise permissions.PermissionDenied("Only shippers can create parcels.")
        serializer.save(shipper=self.request.user)

class ParcelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParcelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Parcel.objects.all()

    def get_queryset(self):
        # Restrict access
        user = self.request.user
        if user.profile.role == 'shipper':
            return Parcel.objects.filter(shipper=user)
        elif user.profile.role == 'car_owner':
            # Drivers can see parcels they can accept (pending) or are assigned to
            return Parcel.objects.filter(
                Q(status='pending') | Q(carrier=user)
            )
        return Parcel.objects.none()

    def perform_update(self, serializer):
        # Add logic: Drivers can only update status, Shippers can edit details if pending
        # For simplicity in this v1, we allow updates but validation should be improved for production
        serializer.save()

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

class PublicParcelTrackView(generics.RetrieveAPIView):
    """
    Public endpoint to track a parcel by its tracking number.
    No authentication required.
    """
    serializer_class = PublicParcelSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Parcel.objects.all()
    lookup_field = 'tracking_number'