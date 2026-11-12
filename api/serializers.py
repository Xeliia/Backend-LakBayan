from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import (
    FarePolicy,
    FareProduct,
    GenderChoices,
    PassengerType,
    Region,
    City,
    Terminal,
    ModeOfTransport,
    Route,
    RouteStop,
    UserProfile,
)

EXPORT_FORMAT_VERSION = 2
EXPORT_CURRENCY = 'PHP'

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    gender = serializers.ChoiceField(choices=GenderChoices.choices, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'gender']

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
        gender = validated_data.pop('gender', GenderChoices.PREFER_NOT_TO_SAY)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        UserProfile.objects.filter(user=user).update(gender=gender)

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
    gender = serializers.ChoiceField(
        choices=GenderChoices.choices,
        source='profile.gender',
        required=False,
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'gender']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().update(instance, validated_data)
        if 'gender' in profile_data:
            UserProfile.objects.update_or_create(
                user=instance,
                defaults={'gender': profile_data['gender']},
            )
        return instance

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
            'id', 'station_id', 'stop_name', 'fare', 'distance',
            'distance_from_previous', 'time', 'time_from_previous', 'order',
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
    fare_policy = serializers.CharField(source='fare_policy_id', read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'destination_name', 'line_id', 'direction', 'mode',
            'fare_policy', 'verified', 'description', 'polyline',
            'stops', 'added_by'
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
            'id', 'station_id', 'name', 'description', 'latitude', 'longitude',
            'city', 'verified', 'rating', 'routes', 'added_by'
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
            'station_id', 'name', 'description', 'latitude', 'longitude', 'city'
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
            'terminal', 'destination_name', 'line_id', 'direction', 'mode',
            'fare_policy', 'description', 'polyline'
        ]

    def validate_terminal(self, value):
        if not value.verified:
            raise serializers.ValidationError("Can only add routes to verified terminals")
        return value

    def validate(self, attrs):
        fare_policy = attrs.get('fare_policy')
        mode = attrs.get('mode')
        if fare_policy and mode and fare_policy.policy_type != mode.fare_type:
            raise serializers.ValidationError({
                'fare_policy': 'Fare policy type must match the transport mode fare type.'
            })
        return attrs

class RouteStopContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = [
            'route', 'station_id', 'stop_name', 'terminal', 'fare', 'distance',
            'distance_from_previous', 'time', 'time_from_previous', 'order',
            'latitude', 'longitude'
        ]
        extra_kwargs = {
            'latitude': {'required': False},
            'longitude': {'required': False},
            'terminal': {'required': False},
            'station_id': {'required': False},
            'distance_from_previous': {'required': False},
            'time_from_previous': {'required': False},
        }
    
    def validate(self, data): # type: ignore
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
    
# For user LP info
class UserLakbayPointsSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source='id')
    username = serializers.CharField()
    lakbay_points = serializers.SerializerMethodField()
    verified_terminals = serializers.SerializerMethodField()
    verified_routes = serializers.SerializerMethodField()
    
    def get_lakbay_points(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.lakbay_points
        return 0
    
    def get_verified_terminals(self, obj):
        return obj.added_terminals.filter(verified=True).count()
    
    def get_verified_routes(self, obj):
        return obj.added_routes.filter(verified=True).count()

# For pie chart
class LakbayPieChartSerializer(serializers.Serializer):
    username = serializers.CharField()
    lakbay_points = serializers.IntegerField()
    percentage = serializers.FloatField()
    verified_terminals = serializers.IntegerField()


class FarePolicySerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='policy_type', read_only=True)
    passenger_type = serializers.CharField(source='passenger_type.code', allow_null=True, read_only=True)
    stations = serializers.SerializerMethodField()

    class Meta:
        model = FarePolicy
        fields = [
            'type', 'media', 'passenger_type', 'stations', 'values',
            'base_fare', 'base_distance_km', 'increment_fare',
            'increment_distance_km', 'maximum_fare', 'rounding', 'description',
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.policy_type == 'distance_based':
            for field in ('stations', 'values'):
                representation.pop(field, None)
        else:
            for field in (
                'base_fare', 'base_distance_km', 'increment_fare',
                'increment_distance_km', 'maximum_fare', 'rounding', 'description',
            ):
                representation.pop(field, None)
        return representation

    def get_stations(self, obj):
        return list(obj.stations.values_list('station_id', flat=True))


class PassengerTypeSerializer(serializers.ModelSerializer):
    discount = serializers.SerializerMethodField()

    class Meta:
        model = PassengerType
        fields = ['discount']

    def get_discount(self, obj):
        return {
            'type': obj.discount_type,
            'value': float(obj.discount_value),
        }


class FareProductSerializer(serializers.ModelSerializer):
    passenger_types = serializers.SerializerMethodField()
    fare_policy = serializers.CharField(source='fare_policy_id', allow_null=True, read_only=True)

    class Meta:
        model = FareProduct
        fields = ['display_name', 'payment_method', 'passenger_types', 'fare_policy']

    def get_passenger_types(self, obj):
        return list(obj.passenger_types.values_list('code', flat=True))


def serialize_fare_configuration():
    """Return normalized fare configuration for the versioned complete export."""
    passenger_types = {
        passenger_type.code: PassengerTypeSerializer(passenger_type).data
        for passenger_type in PassengerType.objects.all()
    }
    fare_products = {
        product.product_id: FareProductSerializer(product).data
        for product in FareProduct.objects.prefetch_related('passenger_types').all()
    }
    fare_policies = {
        policy.policy_id: FarePolicySerializer(policy).data
        for policy in FarePolicy.objects.select_related('passenger_type').prefetch_related('stations').all()
    }
    return {
        'passenger_types': passenger_types,
        'fare_products': fare_products,
        'fare_policies': fare_policies,
    }