from django.contrib import admin
from django.core.management import call_command
from django.contrib import messages
from django.urls import path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from .models import (
    CachedExport,
    City,
    FarePolicy,
    FarePolicyStation,
    FareProduct,
    ModeOfTransport,
    PassengerType,
    Region,
    Route,
    RouteStop,
    Terminal,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'lakbay_points', 'verified_terminals_count', 'verified_routes_count')
    search_fields = ('user__username', 'user__email')
    ordering = ('-lakbay_points',)
    readonly_fields = ('user',)
    
    def verified_terminals_count(self, obj):
        return obj.user.added_terminals.filter(verified=True).count()
    verified_terminals_count.short_description = 'Verified Terminals' # type: ignore
    
    def verified_routes_count(self, obj):
        return obj.user.added_routes.filter(verified=True).count()
    verified_routes_count.short_description = 'Verified Routes' # type: ignore


@admin.register(PassengerType)
class PassengerTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value')
    list_filter = ('discount_type',)
    search_fields = ('code',)


class FarePolicyStationInline(admin.TabularInline):
    model = FarePolicyStation
    extra = 1
    ordering = ('order',)


@admin.register(FarePolicy)
class FarePolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_id', 'policy_type', 'media', 'passenger_type')
    list_filter = ('policy_type', 'media', 'passenger_type')
    search_fields = ('policy_id', 'media')
    fields = (
        'policy_id', 'policy_type', 'media', 'passenger_type', 'values',
        'base_fare', 'base_distance_km', 'increment_fare',
        'increment_distance_km', 'maximum_fare', 'rounding', 'description',
    )
    inlines = [FarePolicyStationInline]


@admin.register(FareProduct)
class FareProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'display_name', 'payment_method', 'fare_policy')
    list_filter = ('payment_method', 'fare_policy')
    search_fields = ('product_id', 'display_name')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'region')
    list_filter = ('region',)
    search_fields = ('name',)


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'station_id', 'name', 'city', 'latitude', 'longitude',
        'verified', 'rating', 'added_by', 'created_at'
    )
    list_filter = ('verified', 'city', 'added_by')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)


@admin.register(ModeOfTransport)
class ModeOfTransportAdmin(admin.ModelAdmin):
    list_display = ['mode_name', 'fare_type', '__str__']
    list_filter = ['mode_name', 'fare_type']
    ordering = ['mode_name', 'fare_type']


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = (
        'order', 'station_id', 'stop_name', 'terminal', 'fare', 'distance',
        'distance_from_previous', 'time', 'time_from_previous',
        'latitude', 'longitude',
    )
    ordering = ('order',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'line_id', 'direction', 'mode', 'fare_policy', 'verified', 'added_by']
    list_filter = ['mode', 'fare_policy', 'verified', 'terminal__city']
    search_fields = ['terminal__name', 'destination_name', 'line_id', 'description']
    inlines = [RouteStopInline]
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "terminal":
            kwargs["queryset"] = Terminal.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = [
        'route', 'order', 'station_id', 'stop_name', 'terminal', 'fare',
        'distance_from_previous', 'time_from_previous', 'latitude', 'longitude',
    ]
    list_filter = ['route__terminal', 'terminal']
    ordering = ['route', 'order']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "terminal":
            # Make it clear that terminal is optional
            kwargs["empty_label"] = "--- No Terminal (Regular Stop) ---"
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(CachedExport)
class CachedExportAdmin(admin.ModelAdmin):
    list_display = ('export_type', 'data_version', 'last_updated', 'file_size_kb', 'record_count')
    list_filter = ('export_type', 'last_updated')
    readonly_fields = ('last_updated', 'file_size_kb', 'record_count', 'data_version')
    change_list_template = 'admin/cached_export_changelist.html'
    
    actions = ['refresh_all_caches']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backup-to-supabase/', self.admin_site.admin_view(self.backup_to_supabase_view), name='backup_to_supabase'),
        ]
        return custom_urls + urls
    
    def backup_to_supabase_view(self, request):
        """Backup transport data from /api/complete/ to Supabase Storage"""
        import requests as http_requests
        
        try:
            # Fetch data from the legacy API endpoint (not cached)
            api_url = 'https://api-lakbayan.onrender.com/api/complete/'
            response = http_requests.get(api_url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Upload to Supabase
            from api.utils.supabase_backup import backup_transport_data
            result = backup_transport_data(data)
            
            self.message_user(
                request,
                f"Backup successful! Uploaded {result['filename']} to Supabase bucket '{result['bucket']}'",
                messages.SUCCESS
            )
        except ImportError:
            self.message_user(
                request,
                "Supabase package not installed. Run: pip install supabase",
                messages.ERROR
            )
        except Exception as e:
            self.message_user(
                request,
                f"Backup failed: {str(e)}",
                messages.ERROR
            )
        
        return HttpResponseRedirect("../")
    
    def refresh_all_caches(self, request, queryset):
        """Refresh all export caches"""
        try:
            call_command('update_export_cache')
            self.message_user(request, "All caches refreshed successfully!")
        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level='ERROR')
    refresh_all_caches.short_description = "Refresh All Export Caches" # type: ignore
    
    def has_add_permission(self, request):
        return False