from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from allauth.account.models import EmailAddress
from functools import wraps
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.db.models import Max
from django.db import transaction
from .models import Terminal, Region, Route, ModeOfTransport, City, RouteStop, CachedExport
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    RegionSerializer,
    TerminalSerializer,
    RouteSerializer,
    TerminalContributionSerializer,
    RouteContributionSerializer,
    RouteStopContributionSerializer,
)

#Account System
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Try to send verification email, but don't fail registration if it errors
        email_sent = False
        email_error = None
        try:
            email_address, _ = EmailAddress.objects.get_or_create(
                user=user, email=user.email, defaults={'primary': True}
            )
            if not email_address.verified:
                email_address.send_confirmation(request, signup=True)
                email_sent = True
        except Exception as e:
            # Log the error but don't fail registration
            email_error = str(e)
            print(f"❌ Email sending failed: {email_error}")
        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        response_data = {
            'message': 'Account Created Successfully',
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined
            }
        }
        
        # Add email status to response
        if email_sent:
            response_data['email_verification'] = 'sent'
        else:
            response_data['email_verification'] = 'failed'
            response_data['email_error'] = email_error
            response_data['note'] = 'Account created but verification email failed. Please contact support.'

        return Response(response_data, status=status.HTTP_201_CREATED)
    
def email_verified_required(view_func):
    """Decorator to require email verification for contributions"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required',
                'code': 'AUTHENTICATION_REQUIRED'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user has verified email
        if not request.user.emailaddress_set.filter(verified=True).exists():
            return Response({
                'error': 'Email verification required',
                'message': 'Please verify your email address before contributing',
                'code': 'EMAIL_VERIFICATION_REQUIRED',
                'action': {
                    'type': 'resend_verification',
                    'url': '/accounts/email/'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    return wrapper

class LoginView(APIView):
    permission_classes = [AllowAny]
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
    
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    permission_classes = [AllowAny]
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email address is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset link (adjust domain as needed)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        
        # Send email
        subject = 'LakBayan - Password Reset Request'
        message = f"""
        Hi {user.username},
        
        You requested to reset your password for your LakBayan account.
        
        Click the link below to reset your password:
        {reset_link}
        
        If you didn't request this, please ignore this email.
        
        Thanks,
        LakBayan Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'Password reset email sent successfully',
            'email': email
        })
        
    except User.DoesNotExist:
        return Response({
            'message': 'If this email exists, a password reset link has been sent'
        })
    
    except Exception as e:
        return Response({
            'error': 'Failed to send reset email',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reset_password(request, uid, token):
    """Handle reset password via URL parameters"""
    if request.method == 'GET':
        # Validate token and show it's valid
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                return Response({
                    'valid': True,
                    'username': user.username,
                    'message': 'Valid reset link. Please provide new password.'
                })
            else:
                return Response({
                    'valid': False,
                    'error': 'Invalid or expired reset token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                'valid': False,
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'POST':
        # Actually reset the password
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response({
                'error': 'new_password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                if len(new_password) < 8:
                    return Response({
                        'error': 'Password must be at least 8 characters long'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'message': 'Password reset successfully',
                    'username': user.username
                })
            else:
                return Response({
                    'error': 'Invalid or expired reset token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    def update(self, request, *args, **kwargs):
        """Override update to handle email changes properly"""
        user = self.get_object()
        old_email = user.email # type: ignore
        
        # Get the serializer and validate
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        new_email = serializer.validated_data.get('email')
        
        # If email is being changed
        if new_email and new_email != old_email:
            # Check if new email already exists
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                return Response({
                    'error': 'Email address already in use'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save the user first
            user = serializer.save()
            
            # Handle EmailAddress model
            try:
                # Remove old email verification
                EmailAddress.objects.filter(user=user, email=old_email).delete()
                
                # Create new unverified email address
                new_email_obj, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=new_email,
                    defaults={'primary': True, 'verified': False}
                )
                
                # Send verification email for new email
                new_email_obj.send_confirmation(request, signup=False)
                
                return Response({
                    'message': 'Profile updated successfully',
                    'email_changed': True,
                    'verification_required': True,
                    'note': 'Please verify your new email address',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'email_verified': False  # Now unverified
                    }
                })
                
            except Exception as e:
                # If email handling fails, revert user email
                user.email = old_email
                user.save()
                return Response({
                    'error': 'Failed to update email verification',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            # No email change, normal update
            user = serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'email_changed': False,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            })
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_new_password = request.data.get('confirm_new_password')
    
    if not all([old_password, new_password, confirm_new_password]):
        return Response({
            'error': 'old_password, new_password, and confirm_new_password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Verify current password
    if not user.check_password(old_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if new passwords match
    if new_password != confirm_new_password:
        return Response({
            'error': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password strength
    if len(new_password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if new password is different from current
    if user.check_password(new_password):
        return Response({
            'error': 'New password must be different from current password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully',
            'username': user.username,
            'note': 'Please login again with your new password'
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to change password',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        password = request.data.get("password")
        user = request.user

        if not user.check_password(password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({"message": "Account deleted successfully"}, status=status.HTTP_200_OK)
    

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
def metadata(request):
    """Lightweight endpoint to check if data has changed"""
    
    # Check what timestamp fields are available and use them
    terminal_timestamp = None
    route_timestamp = None
    
    # Try to get the latest terminal
    if Terminal.objects.filter(verified=True).exists():
        latest_terminal = Terminal.objects.filter(verified=True).latest('created_at')
        terminal_timestamp = latest_terminal.created_at
    
    # Try to get the latest route  
    if Route.objects.filter(verified=True).exists():
        latest_route = Route.objects.filter(verified=True).latest('created_at')
        route_timestamp = latest_route.created_at
    
    # Find the most recent
    all_timestamps = [terminal_timestamp, route_timestamp]
    global_last_updated = max([ts for ts in all_timestamps if ts is not None], default=timezone.now())
    
    # Get counts
    total_terminals = Terminal.objects.filter(verified=True).count()
    total_routes = Route.objects.filter(verified=True).count()
    total_stops = RouteStop.objects.filter(route__verified=True).count()
    
    return Response({
        "last_updated": global_last_updated,
        "data_version": global_last_updated.strftime("%Y%m%d_%H%M%S"),
        "counts": {
            "terminals": total_terminals,
            "routes": total_routes, 
            "stops": total_stops
        },
        "check_timestamp": timezone.now()
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
    lng_range = radius / (111 * max(abs(float(lat)), 0.01))
    
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
@email_verified_required
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
@email_verified_required
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
@email_verified_required
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
@email_verified_required
def contribute_complete_route(request):
    """Submit route with multiple stops to verified terminal"""
    data = request.data
    
    # Validate required structure
    if not all(key in data for key in ['route', 'stops']):
        return Response({
            'error': 'Required structure: {"route": {...}, "stops": [...]}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not isinstance(data['stops'], list) or len(data['stops']) == 0:
        return Response({
            'error': 'At least one stop is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # 1. Validate terminal exists and is verified
            terminal_id = data['route']['terminal']
            try:
                terminal = Terminal.objects.get(id=terminal_id, verified=True)
            except Terminal.DoesNotExist:
                return Response({
                    'error': 'Terminal must exist and be verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Create Route (unverified) - USE DIRECT MODEL CREATION
            route = Route.objects.create(
                terminal=terminal,
                destination_name=data['route']['destination_name'],
                mode_id=data['route']['mode'],
                description=data['route'].get('description', ''),
                polyline=data['route'].get('polyline'),
                added_by=request.user,
                verified=False
            )
            
            print(f"✅ Route created: ID={route.id}")  # type: ignore # Debug
            
            # 3. Create Stops - USE DIRECT MODEL CREATION
            created_stops = []
            for i, stop_data in enumerate(data['stops']):
                # Validate required fields
                required_fields = ['stop_name', 'fare', 'latitude', 'longitude']
                missing_fields = [field for field in required_fields if field not in stop_data]
                if missing_fields:
                    return Response({
                        'error': f'Missing required fields in stop {i}: {missing_fields}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create stop directly
                stop = RouteStop.objects.create(
                    route=route,  # Pass the route object directly
                    stop_name=stop_data['stop_name'],
                    fare=stop_data['fare'],
                    distance=stop_data.get('distance'),
                    time=stop_data.get('time'),
                    order=stop_data.get('order', i + 1),
                    latitude=stop_data['latitude'],
                    longitude=stop_data['longitude'],
                    terminal_id=stop_data.get('terminal')  # Optional terminal reference
                )
                
                created_stops.append(stop)
                print(f"✅ Stop created: ID={stop.id}, Route ID={stop.route_id}")  # type: ignore # Debug
            
            return Response({
                'message': 'Complete route with stops submitted successfully',
                'route_id': route.id, # type: ignore
                'stops_count': len(created_stops),
                'status': 'pending_verification'
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        print(f"❌ Error in contribute_complete_route: {str(e)}")  # Debug
        return Response({
            'error': 'Failed to create complete route',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@email_verified_required
def contribute_all(request):
    """Submit terminal, route, and stops all together"""
    data = request.data
    
    # Validate required structure
    if not all(key in data for key in ['terminal', 'route', 'stops']):
        return Response({
            'error': 'Required structure: {"terminal": {...}, "route": {...}, "stops": [...]}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not isinstance(data['stops'], list) or len(data['stops']) == 0:
        return Response({
            'error': 'At least one stop is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # 1. Create Terminal (unverified) - DIRECT MODEL CREATION
            terminal_data = data['terminal']
            
            # Validate required terminal fields
            required_terminal_fields = ['name', 'latitude', 'longitude', 'city']
            missing_fields = [field for field in required_terminal_fields if field not in terminal_data]
            if missing_fields:
                return Response({
                    'error': f'Missing required terminal fields: {missing_fields}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            terminal = Terminal.objects.create(
                name=terminal_data['name'],
                description=terminal_data.get('description', ''),
                latitude=terminal_data['latitude'],
                longitude=terminal_data['longitude'],
                city_id=terminal_data['city'],
                added_by=request.user,
                verified=False,
                rating=0
            )
            
            print(f"✅ Terminal created: ID={terminal.id}")  # type: ignore # Debug
            
            # 2. Create Route (unverified) - DIRECT MODEL CREATION
            route_data = data['route']
            
            # Validate required route fields
            required_route_fields = ['destination_name', 'mode']
            missing_fields = [field for field in required_route_fields if field not in route_data]
            if missing_fields:
                return Response({
                    'error': f'Missing required route fields: {missing_fields}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            route = Route.objects.create(
                terminal=terminal,
                destination_name=route_data['destination_name'],
                mode_id=route_data['mode'],
                description=route_data.get('description', ''),
                polyline=route_data.get('polyline'),
                added_by=request.user,
                verified=False
            )
            
            print(f"✅ Route created: ID={route.id}")  # type: ignore # Debug
            
            # 3. Create Stops - DIRECT MODEL CREATION
            created_stops = []
            for i, stop_data in enumerate(data['stops']):
                # Validate required stop fields
                required_stop_fields = ['stop_name', 'fare', 'latitude', 'longitude']
                missing_fields = [field for field in required_stop_fields if field not in stop_data]
                if missing_fields:
                    return Response({
                        'error': f'Missing required fields in stop {i}: {missing_fields}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create stop directly
                stop = RouteStop.objects.create(
                    route=route,
                    stop_name=stop_data['stop_name'],
                    fare=stop_data['fare'],
                    distance=stop_data.get('distance'),
                    time=stop_data.get('time'),
                    order=stop_data.get('order', i + 1),
                    latitude=stop_data['latitude'],
                    longitude=stop_data['longitude'],
                    terminal_id=stop_data.get('terminal')
                )
                
                created_stops.append(stop)
                print(f"✅ Stop created: ID={stop.id}, Route ID={stop.route_id}")  # type: ignore # Debug
            
            return Response({
                'message': 'Complete transportation data submitted successfully',
                'status': 'pending_verification',
                'data': {
                    'terminal_id': terminal.id, # type: ignore
                    'route_id': route.id, # type: ignore
                    'stops_count': len(created_stops),
                    'terminal_name': terminal.name,
                    'route_destination': route.destination_name,
                    'all_unverified': True,
                    'note': 'All submissions require admin approval before becoming public'
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        print(f"❌ Error in contribute_all: {str(e)}")  # Debug
        return Response({
            'error': 'Failed to create complete transportation data',
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_email_verification_status(request):
    """Check if user's email is verified"""
    user = request.user
    verified_email = user.emailaddress_set.filter(verified=True).first()
    
    return Response({
        'email_verified': bool(verified_email),
        'email': verified_email.email if verified_email else None,
        'username': user.username,
        'primary_email': user.email
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email(request):
    """Resend email verification"""
    from allauth.account.models import EmailAddress
    
    user = request.user
    
    # Get or create email address
    email_address, created = EmailAddress.objects.get_or_create(
        user=user,
        email=user.email,
        defaults={'primary': True, 'verified': False}
    )
    
    if email_address.verified:
        return Response({
            'message': 'Email is already verified',
            'email_verified': True
        })
    
    try:
        # Modern Allauth way
        email_address.send_confirmation(request, signup=False)
        
        return Response({
            'message': 'Verification email sent successfully',
            'email': email_address.email
        })
    except Exception as e:
        return Response({
            'error': 'Failed to send verification email',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def cached_complete_export(request):
    """Serve cached complete export from JSONB"""
    try:
        cached = CachedExport.objects.get(export_type='complete')
        return Response(cached.data)
    except CachedExport.DoesNotExist:
        return Response({
            'error': 'Cache not initialized',
            'message': 'Please run: python manage.py update_export_cache',
            'fallback': '/api/complete/'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
def cached_terminals_export(request):
    """Serve cached terminals export from JSONB"""
    try:
        cached = CachedExport.objects.get(export_type='terminals')
        return Response(cached.data)
    except CachedExport.DoesNotExist:
        return Response({
            'error': 'Cache not initialized',
            'fallback': '/api/export/terminals/'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
def cached_routes_export(request):
    """Serve cached routes export from JSONB"""
    try:
        cached = CachedExport.objects.get(export_type='routes')
        return Response(cached.data)
    except CachedExport.DoesNotExist:
        return Response({
            'error': 'Cache not initialized',
            'fallback': '/api/export/routes-stops/'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
def cached_regions_export(request):
    """Serve cached regions export from JSONB"""
    try:
        cached = CachedExport.objects.get(export_type='regions')
        return Response(cached.data)
    except CachedExport.DoesNotExist:
        return Response({
            'error': 'Cache not initialized',
            'fallback': '/api/export/regions-cities/'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
def cached_metadata(request):
    """Get cache status and metadata"""
    try:
        complete_cache = CachedExport.objects.get(export_type='complete')
        
        # Get all cache info
        all_caches = CachedExport.objects.all()
        cache_info = {
            cache.export_type: {
                'data_version': cache.data_version,
                'last_updated': cache.last_updated,
                'file_size_kb': cache.file_size_kb,
                'record_count': cache.record_count
            }
            for cache in all_caches
        }
        
        return Response({
            'cached': True,
            'primary_version': complete_cache.data_version,
            'last_updated': complete_cache.last_updated,
            'caches': cache_info,
            'endpoints': {
                'complete': '/api/cached/complete/',
                'terminals': '/api/cached/terminals/',
                'routes': '/api/cached/routes/',
                'regions': '/api/cached/regions/'
            }
        })
    except CachedExport.DoesNotExist:
        return Response({
            'cached': False,
            'message': 'Cache not initialized',
            'live_endpoints': {
                'complete': '/api/complete/',
                'terminals': '/api/export/terminals/',
                'routes': '/api/export/routes-stops/',
                'regions': '/api/export/regions-cities/'
            }
        })