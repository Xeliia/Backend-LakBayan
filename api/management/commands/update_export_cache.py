from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import CachedExport, Region, Terminal, Route
from api.serializers import RegionSerializer, TerminalSerializer, RouteSerializer

class Command(BaseCommand):
    help = 'Update cached JSON exports in database'

    def handle(self, *args, **options):
        timestamp = timezone.now()
        version = timestamp.strftime("%Y%m%d_%H%M%S")
        
        self.stdout.write(self.style.SUCCESS("Updating export cache..."))
        
        # 1. Complete Export
        self.stdout.write("Generating complete export...")
        regions = Region.objects.prefetch_related(
            'city_set__terminals__origin_routes__stops',
            'city_set__terminals__origin_routes__mode'
        ).all()
        
        complete_data = {
            'regions': RegionSerializer(regions, many=True).data,
            'last_updated': timestamp.isoformat(),
            'data_version': version,
            'total_terminals': Terminal.objects.filter(verified=True).count(),
            'total_routes': Route.objects.filter(verified=True).count(),
        }
        
        cache_obj, created = CachedExport.objects.update_or_create(
            export_type='complete',
            defaults={
                'data': complete_data,
                'data_version': version
            }
        )
        cache_obj.update_metadata()
        self.stdout.write(self.style.SUCCESS(f"Complete: {cache_obj.file_size_kb}KB"))
        
        # 2. Terminals Only
        self.stdout.write("Generating terminals export...")
        terminals = Terminal.objects.filter(verified=True).select_related(
            "city__region"
        ).prefetch_related(
            "origin_routes__mode",
            "origin_routes__stops"
        )
        
        terminals_data = {
            'terminals': TerminalSerializer(terminals, many=True).data,
            'export_timestamp': timestamp.isoformat()
        }
        
        cache_obj, created = CachedExport.objects.update_or_create(
            export_type='terminals',
            defaults={
                'data': terminals_data,
                'data_version': version
            }
        )
        cache_obj.update_metadata()
        self.stdout.write(self.style.SUCCESS(f"Terminals: {cache_obj.file_size_kb}KB"))
        
        # 3. Routes Only
        self.stdout.write("Generating routes export...")
        routes = Route.objects.filter(verified=True).prefetch_related(
            "stops", "mode", "terminal"
        )
        
        routes_data = {
            'routes': RouteSerializer(routes, many=True).data,
            'export_timestamp': timestamp.isoformat()
        }
        
        cache_obj, created = CachedExport.objects.update_or_create(
            export_type='routes',
            defaults={
                'data': routes_data,
                'data_version': version
            }
        )
        cache_obj.update_metadata()
        self.stdout.write(self.style.SUCCESS(f"Routes: {cache_obj.file_size_kb}KB"))
        
        # 4. Regions/Cities Only
        self.stdout.write("Generating regions export...")
        regions_simple = Region.objects.prefetch_related("city_set")
        
        regions_data = {
            'regions': RegionSerializer(regions_simple, many=True).data,
            'export_timestamp': timestamp.isoformat()
        }
        
        cache_obj, created = CachedExport.objects.update_or_create(
            export_type='regions',
            defaults={
                'data': regions_data,
                'data_version': version
            }
        )
        cache_obj.update_metadata()
        self.stdout.write(self.style.SUCCESS(f"Regions: {cache_obj.file_size_kb}KB"))
        
        self.stdout.write(self.style.SUCCESS(f"\nAll exports cached! Version: {version}"))