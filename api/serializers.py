from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Region, City, Terminal, ModeOfTransport, Route, RouteStop

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already exists")
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

        return user
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password")
            if not user.is_active:
                raise serializers.ValidationError("Account is disabled")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must include username and password")

        return attrs
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']

    def validate_username(self, value):
        """Ensure username is unique"""
        user = self.instance
        if user and User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Username already taken")
        return value
    
    def validate_email(self, value):
        """Ensure email is unique"""
        user = self.instance
        if user and User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already in use")
        return value

class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = [
            'id', 'stop_name', 'fare', 'distance', 'time', 'order',
            'latitude', 'longitude', 'terminal'
        ]

class ModeOfTransportSerializer(serializers.ModelSerializer):
    mode_display = serializers.CharField(source='get_mode_name_display', read_only=True)
    
    class Meta:
        model = ModeOfTransport
        fields = ['id', 'mode_name', 'mode_display', 'fare_type']

class RouteSerializer(serializers.ModelSerializer):
    mode = ModeOfTransportSerializer(read_only=True)
    stops = RouteStopSerializer(many=True, read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'mode', 'verified', 'description', 
            'polyline', 'stops'
        ]

class BasicCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'region']

class TerminalSerializer(serializers.ModelSerializer):
    city = BasicCitySerializer(read_only=True)
    routes = serializers.SerializerMethodField()
    
    class Meta:
        model = Terminal
        fields = [
            'id', 'name', 'description', 'latitude', 'longitude',
            'city', 'verified', 'rating', 'routes'
        ]
    
    def get_routes(self, obj):
        routes = obj.origin_routes.filter(verified=True)
        return RouteSerializer(routes, many=True).data
    
class CitySerializer(serializers.ModelSerializer):
    terminals = TerminalSerializer(many=True, read_only=True)
    
    class Meta:
        model = City
        fields = ['id', 'name', 'region', 'terminals']

class RegionSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'cities']
    
    def get_cities(self, obj):
        cities = obj.city_set.prefetch_related(
            'terminals__origin_routes__mode',
            'terminals__origin_routes__stops'
        )
        return CitySerializer(cities, many=True).data
    
# User Contribution
class TerminalContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terminal
        fields = [
            'name', 'description', 'latitude', 'longitude', 'city'
        ]

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value
    
    def validate(self, attrs):
        """Check for duplicate terminals by location"""
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        
        # Check if terminal at same coordinates already exists
        existing_terminal = Terminal.objects.filter(
            latitude=latitude,
            longitude=longitude
        ).first()
        
        if existing_terminal:
            if existing_terminal.verified:
                raise serializers.ValidationError({
                    'location': f'A terminal already exists at coordinates ({latitude}, {longitude}). '
                               f'Terminal name: "{existing_terminal.name}". '
                               f'Please add routes to the existing terminal instead.',
                    'existing_terminal_id': existing_terminal.id, # type: ignore
                    'existing_terminal_name': existing_terminal.name,
                    'suggestion': 'Use /contribute/route/ to add routes to existing terminals'
                })
            else:
                raise serializers.ValidationError({
                    'location': f'A terminal is already pending verification at coordinates ({latitude}, {longitude}). '
                               f'Terminal name: "{existing_terminal.name}".',
                    'existing_terminal_id': existing_terminal.id, # type: ignore
                    'existing_terminal_name': existing_terminal.name,
                    'suggestion': 'Wait for admin approval or contact support'
                })
        
        return attrs

class RouteContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = [
            'terminal', 'destination_name', 'mode', 'description', 'polyline'
        ]

    def validate_terminal(self, value):
        if not value.verified:
            raise serializers.ValidationError("Can only add routes to verified terminals")
        return value

class RouteStopContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = [
            'route', 'stop_name', 'terminal', 'fare', 'distance', 
            'time', 'order', 'latitude', 'longitude'
        ]
        extra_kwargs = {
            'latitude': {'required': False},
            'longitude': {'required': False},
            'terminal': {'required': False},
        }
    
    def validate(self, data):
        """
        Custom validation to ensure we have location data from SOMEWHERE
        (either a linked Terminal or manual Coordinates).
        """
        terminal = data.get('terminal')
        lat = data.get('latitude')
        lng = data.get('longitude')

        # Logic: If no terminal is provided, you MUST provide coordinates
        if not terminal and (lat is None or lng is None):
            raise serializers.ValidationError(
                "If not linked to a Terminal, you MUST provide 'latitude' and 'longitude'."
            )
        return data

    def validate_route(self, value):
        if not value.verified:
            raise serializers.ValidationError("Can only add stops to verified routes")
        return value

    def validate_order(self, value):
        route = self.initial_data.get('route') # type: ignore
        if route and RouteStop.objects.filter(route=route, order=value).exists():
            raise serializers.ValidationError("A stop with this order already exists for this route")
        return value