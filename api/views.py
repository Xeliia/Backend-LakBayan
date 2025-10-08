from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.db.models import Max
from django.db import transaction
from .models import Terminal, Region, Route, ModeOfTransport, City, RouteStop
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    RegionSerializer,
    ModeOfTransportSerializer,
    TerminalSerializer,
    RouteSerializer,
    RouteStopSerializer,
    TerminalContributionSerializer,
    RouteContributionSerializer,
    RouteStopContributionSerializer,
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
    terminal_last_updated = Terminal.objects.aggregate(Max('updated_at'))['updated_at__max']
    
    # Get metadata
    last_updated = terminal_last_updated or timezone.now()
    
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
    last_updated = Terminal.objects.aggregate(Max('updated_at'))['updated_at__max'] or timezone.now()
    
    total_terminals = Terminal.objects.filter(verified=True).count()
    total_routes = Route.objects.filter(verified=True).count()
    
    return Response({
        'last_updated': last_updated,
        'total_terminals': total_terminals,
        'total_routes': total_routes,
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

# Seperate Exports
@api_view(['GET'])
def export_regions_cities(request):
    regions = Region.objects.prefetch_related("city_set").all()
    data = RegionSerializer(regions, many=True).data
    return Response({
        "regions": data,
        "export_timestamp": timezone.now()
    })


# 2. Terminals
@api_view(['GET'])
def export_terminals(request):
    terminals = Terminal.objects.select_related("city__region").prefetch_related(
        "origin_routes__mode",
        "origin_routes__stops"
    ).all()
    data = TerminalSerializer(terminals, many=True).data
    return Response({
        "terminals": data,
        "last_updated": Terminal.objects.aggregate(Max("updated_at"))["updated_at__max"],
        "export_timestamp": timezone.now()
    })


# 3. Routes + Stops
@api_view(['GET'])
def export_routes_stops(request):
    routes = Route.objects.prefetch_related("stops", "mode", "terminal").all()
    data = RouteSerializer(routes, many=True).data
    return Response({
        "routes": data,
        "export_timestamp": timezone.now()
    })

# User Contribution

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contribute_terminal(request):
    """Allow users to contribute new terminals"""
    serializer = TerminalContributionSerializer(data=request.data)
    if serializer.is_valid():
        # Auto-set fields according to your model
        terminal = serializer.save(
            added_by=request.user,
            verified=False,  # Admin will verify later
            rating=0  # Default rating
        )
        return Response({
            'message': 'Terminal contribution submitted successfully',
            'terminal_id': terminal.id, # type: ignore
            'status': 'pending_verification',
            'data': TerminalContributionSerializer(terminal).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contribute_route(request):
    """Allow users to contribute new routes to verified terminals"""
    serializer = RouteContributionSerializer(data=request.data)
    if serializer.is_valid():
        route = serializer.save(
            added_by=request.user,
            verified=False  # Admin will verify later
        )
        return Response({
            'message': 'Route contribution submitted successfully',
            'route_id': route.id, # type: ignore
            'status': 'pending_verification',
            'data': RouteContributionSerializer(route).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contribute_route_stop(request):
    """Allow users to contribute new stops to verified routes"""
    serializer = RouteStopContributionSerializer(data=request.data)
    if serializer.is_valid():
        # No added_by field for RouteStop as per your model
        route_stop = serializer.save()
        return Response({
            'message': 'Route stop contribution submitted successfully',
            'stop_id': route_stop.id, # type: ignore
            'data': RouteStopContributionSerializer(route_stop).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contribute_complete_route(request):
    """Allow users to contribute a route with multiple stops in one request"""
    route_data = request.data.get('route', {})
    stops_data = request.data.get('stops', [])
    
    if not route_data:
        return Response({'error': 'Route data is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create the route
            route_serializer = RouteContributionSerializer(data=route_data)
            if route_serializer.is_valid():
                route = route_serializer.save(
                    added_by=request.user,
                    verified=False
                )
                
                # Create the stops
                created_stops = []
                for stop_data in stops_data:
                    stop_data['route'] = route.id # type: ignore
                    stop_serializer = RouteStopContributionSerializer(data=stop_data)
                    if stop_serializer.is_valid():
                        stop = stop_serializer.save()
                        created_stops.append(stop)
                    else:
                        return Response({
                            'error': 'Invalid stop data',
                            'stop_errors': stop_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'message': 'Complete route with stops submitted successfully',
                    'route_id': route.id, # type: ignore
                    'stops_count': len(created_stops),
                    'status': 'pending_verification'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Invalid route data',
                    'route_errors': route_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        return Response({
            'error': 'Failed to create route with stops',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# User's Contributions
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_contributions(request):
    """Get current user's contributions"""
    terminals = Terminal.objects.filter(added_by=request.user).select_related('city__region')
    routes = Route.objects.filter(added_by=request.user).select_related('terminal', 'mode')
    
    return Response({
        'terminals': {
            'data': TerminalContributionSerializer(terminals, many=True).data,
            'total': terminals.count(),
            'verified': terminals.filter(verified=True).count(),
            'pending': terminals.filter(verified=False).count(),
        },
        'routes': {
            'data': RouteContributionSerializer(routes, many=True).data,
            'total': routes.count(),
            'verified': routes.filter(verified=True).count(),
            'pending': routes.filter(verified=False).count(),
        },
        'summary': {
            'total_contributions': terminals.count() + routes.count(),
            'verified_contributions': terminals.filter(verified=True).count() + routes.filter(verified=True).count(),
        }
    })

# Helper endpoints
@api_view(['GET'])
def get_cities_by_region(request, region_id):
    """Get cities in a specific region for the contribution form"""
    cities = City.objects.filter(region_id=region_id)
    return Response([
        {'id': city.id, 'name': city.name}  # type: ignore
        for city in cities
    ])

@api_view(['GET'])
def get_transport_modes(request):
    """Get available transport modes for the contribution form"""
    modes = ModeOfTransport.objects.all()
    return Response([
        {
            'id': mode.id,  # type: ignore
            'name': mode.get_mode_name_display(), # type: ignore
            'fare_type': mode.get_fare_type_display() # type: ignore
        } 
        for mode in modes
    ])