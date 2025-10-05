from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Terminal
from ..serializers.terminals import TerminalSerializer
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