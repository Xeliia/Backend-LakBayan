from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Max
from .models import Terminal, Region, Route, ModeOfTransport
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    RegionSerializer,
    ModeOfTransportSerializer,
    TerminalSerializer
)

#Account System
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            'message': 'Account Created Successfully',
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined
            }
        }, status=status.HTTP_201_CREATED)
        
class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user'] # type: ignore
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            return Response({
                'message': 'Login Successful',
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Successfully Logged Out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self): # type: ignore
        return self.request.user
    
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        password = request.data.get("password")
        user = request.user

        if not user.check_password(password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({"message": "Account deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    

#Export All Data
@api_view(['GET'])
def complete_data_export(request):
    # Get all regions
    regions = Region.objects.prefetch_related(
        'city_set__terminals__origin_routes__stops',
        'city_set__terminals__origin_routes__mode'
    ).all()
    
    # Get transport modes
    transport_modes = ModeOfTransport.objects.all()
    
    # Get metadata
    last_updated = max(
        Terminal.objects.aggregate(Max('updated_at'))['updated_at__max'] or timezone.now(),
        Route.objects.aggregate(Max('created_at'))['created_at__max'] or timezone.now()
    )
    
    total_terminals = Terminal.objects.filter(verified=True).count()
    total_routes = Route.objects.filter(verified=True).count()
    
    # Serialize data
    regions_data = RegionSerializer(regions, many=True).data
    
    response_data = {
        'regions': regions_data,
        'last_updated': last_updated,
        'total_terminals': total_terminals,
        'total_routes': total_routes,
        'export_timestamp': timezone.now()
    }
    
    return Response(response_data)

@api_view(['GET'])
def data_export_metadata(request):
    last_updated = max(
        Terminal.objects.aggregate(Max('updated_at'))['updated_at__max'] or timezone.now(),
        Route.objects.aggregate(Max('created_at'))['created_at__max'] or timezone.now()
    )
    
    return Response({
        'last_updated': last_updated,
        'total_terminals': Terminal.objects.filter(verified=True).count(),
        'total_routes': Route.objects.filter(verified=True).count(),
    })

#Terminals
class TerminalsByCityView(generics.ListAPIView):
    serializer_class = TerminalSerializer
    
    def get_queryset(self):  # type: ignore
        city_id = self.kwargs.get('city_id')
        return Terminal.objects.filter(
            city_id=city_id,
            verified=True
        ).select_related('city__region').prefetch_related(
            'origin_routes__mode',
            'origin_routes__stops'
        )

class TerminalsByRegionView(generics.ListAPIView):
    serializer_class = TerminalSerializer
    
    def get_queryset(self):  # type: ignore
        region_id = self.kwargs.get('region_id')
        return Terminal.objects.filter(
            city__region_id=region_id,
            verified=True
        ).select_related('city__region').prefetch_related(
            'origin_routes__mode',
            'origin_routes__stops'
        )

@api_view(['GET'])
def nearby_terminals(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius = float(request.GET.get('radius', 25))  # Default 25km
    
    if not lat or not lng:
        return Response({
            'error': 'lat and lng parameters are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Simple bounding box filter
    lat_range = radius / 111  # Rough conversion: 1 degree ≈ 111km
    lng_range = radius / (111 * abs(float(lat)))
    
    terminals = Terminal.objects.filter(
        latitude__range=(float(lat) - lat_range, float(lat) + lat_range),
        longitude__range=(float(lng) - lng_range, float(lng) + lng_range),
        verified=True
    ).select_related('city__region').prefetch_related(
        'origin_routes__mode',
        'origin_routes__stops'
    )
    
    serializer = TerminalSerializer(terminals, many=True)
    return Response(serializer.data)