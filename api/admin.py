from django.contrib import admin
from django.core.management import call_command
from django.contrib import messages
from django.urls import path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from .models import Region, City, Terminal, ModeOfTransport, Route, RouteStop, CachedExport


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
        'id', 'name', 'city', 'latitude', 'longitude',
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
    fields = ('order', 'stop_name', 'terminal', 'fare', 'distance', 'time', 'latitude', 'longitude')
    ordering = ('order',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'mode', 'verified', 'added_by']
    list_filter = ['mode', 'verified', 'terminal__city']
    search_fields = ['terminal__name', 'destination_name', 'description']
    inlines = [RouteStopInline]
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "terminal":
            kwargs["queryset"] = Terminal.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'order', 'stop_name', 'terminal', 'fare', 'latitude', 'longitude']
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