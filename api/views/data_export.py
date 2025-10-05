from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Max
from ..models import Terminal, Region, Route, ModeOfTransport
from ..serializers.terminals import (
    RegionSerializer,
    ModeOfTransportSerializer
)

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
    transport_modes_data = ModeOfTransportSerializer(transport_modes, many=True).data
    
    response_data = {
        'regions': regions_data,
        'transport_modes': transport_modes_data,
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