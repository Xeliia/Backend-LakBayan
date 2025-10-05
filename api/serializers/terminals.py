from rest_framework import serializers
from ..models import Region, City, Terminal, ModeOfTransport, Route, RouteStop

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