from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.db.models import Q
from .models import Parcel, Profile
from .serializers import ParcelSerializer, ProfileSerializer, PublicParcelSerializer
from .pricing import calculate_haversine_distance, get_pricing_breakdown
from decimal import Decimal

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
        from .models import PlatformProfile
        platform_profile = PlatformProfile.objects.first()
        if platform_profile and not platform_profile.accepting_shipments:
             raise permissions.PermissionDenied(platform_profile.maintenance_message or "The platform is currently not accepting new shipments.")
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

class PriceCalculatorView(APIView):
    permission_classes = [permissions.AllowAny] # Allow frontend to query without strict auth if needed, or IsAuthenticated

    def post(self, request):
        try:
            data = request.data
            pickup_lat = data.get('pickup_lat')
            pickup_lng = data.get('pickup_lng')
            delivery_lat = data.get('delivery_lat')
            delivery_lng = data.get('delivery_lng')
            weight = data.get('weight')

            if not all([pickup_lat, pickup_lng, delivery_lat, delivery_lng, weight]):
                return Response({'error': 'Missing location or weight data.'}, status=status.HTTP_400_BAD_REQUEST)

            weight = Decimal(str(weight))
            
            # Calculate Distance
            distance_km = calculate_haversine_distance(pickup_lat, pickup_lng, delivery_lat, delivery_lng)
            
            # Get Breakdown
            breakdown = get_pricing_breakdown(distance_km, weight)
            
            if 'error' in breakdown:
                return Response(breakdown, status=status.HTTP_400_BAD_REQUEST)
            
            response_data = {
                'distance_km': round(float(distance_km), 2),
                'weight_kg': float(weight),
                'price': float(breakdown['price']),
                'platform_fee': float(breakdown['platform_fee']),
                'driver_amount': float(breakdown['driver_amount']),
                'platform_fee_percentage': float(breakdown['platform_fee_percentage']),
            }
            
            return Response(response_data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
