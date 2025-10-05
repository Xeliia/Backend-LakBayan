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
    list_display = ('id', 'mode_name', 'fare_type')
    list_filter = ('fare_type',)
    search_fields = ('mode_name',)


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ('order', 'stop_name', 'terminal', 'fare', 'distance', 'time', 'latitude', 'longitude')
    ordering = ('order',)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'mode', 'terminal', 'verified', 'added_by')
    list_filter = ('verified', 'mode')
    search_fields = ('description', 'terminal__name')
    inlines = [RouteStopInline]


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'route', 'order', 'stop_name',
        'fare', 'distance', 'time', 'latitude', 'longitude'
    )
    list_filter = ('route',)
    search_fields = ('stop_name',)
    ordering = ('route', 'order')
