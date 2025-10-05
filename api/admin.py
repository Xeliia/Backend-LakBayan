from django.contrib import admin
from .models import Region, City, Terminal, ModeOfTransport, Route, RouteStop


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