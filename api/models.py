from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from threading import Thread
import logging

logger = logging.getLogger(__name__)

# Create your models here.

# Regions table
class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Cities Table
class City(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = "Cities"
        unique_together = ('name', 'region')

    def __str__(self):
        return f"{self.name}, {self.region.name}"
    
# Terminals Table
class Terminal(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="terminals")
    verified = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="added_terminals")
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['verified']),
            models.Index(fields=['city']),
        ]
        unique_together = [
            ('latitude', 'longitude'),
        ]

    def __str__(self):
        return self.name or f"Terminal {self.id}" # type: ignore
    
# Mode Of Transport Table
class ModeOfTransport(models.Model):
    MODE_CHOICES = [
        ('tricycle', 'Tricycle'),
        ('tuktuk', 'Tuktuk'),
        ('bus', 'Bus'),
        ('jeepney', 'Jeepney'),
        ('train', 'Train'),
        ('motorcycle', 'Motorcycle'),
    ]

    FARE_TYPE_CHOICES = [
        ('fixed', 'Fixed'),
        ('distance_based', 'Distance Based'),
    ]

    mode_name = models.CharField(max_length=20, choices=MODE_CHOICES)
    fare_type = models.CharField(max_length=20, choices=FARE_TYPE_CHOICES)

    class Meta:
        unique_together = ('mode_name', 'fare_type')
    
    def __str__(self):
        return f"{self.get_mode_name_display()} ({self.get_fare_type_display()})" # type: ignore

# Route Table
class Route(models.Model):
    terminal = models.ForeignKey('Terminal', on_delete=models.CASCADE, related_name='origin_routes')
    destination_name = models.CharField(max_length=200)
    mode = models.ForeignKey('ModeOfTransport', on_delete=models.CASCADE, related_name='routes')
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_routes')
    description = models.TextField(blank=True, null=True)
    polyline = models.JSONField(blank=True, null=True)

    def __str__(self):
        origin_name = self.terminal.name or f'Terminal {self.terminal.id}'
        return f"{origin_name} → {self.destination_name} ({self.mode})"

# Route Stop Tables
class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=200)
    terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, blank=True, related_name='route_stops')
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time = models.IntegerField(null=True, blank=True)
    order = models.PositiveIntegerField()
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ('route', 'order')

    def clean(self):
        """Ensure that if no terminal is selected, lat/long are provided manually."""
        super().clean()
        if not self.terminal and (self.latitude is None or self.longitude is None):
            raise ValidationError("If not linked to a Terminal, you MUST provide Latitude and Longitude.")
    
    def save(self, *args, **kwargs):
        """Auto-fill details from the linked terminal if they are missing."""
        if self.terminal:

            self.latitude = self.terminal.latitude
            self.longitude = self.terminal.longitude
            
            if not self.stop_name:
                self.stop_name = self.terminal.name or "Unnamed Station"
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Stop {self.order}: {self.stop_name} - {self.route}"
    
# Add this at the end of your models.py

class CachedExport(models.Model):
    """Store pre-computed JSON exports for fast frontend access"""
    
    EXPORT_TYPE_CHOICES = [
        ('complete', 'Complete Data Export'),
        ('terminals', 'Terminals Only'),
        ('routes', 'Routes and Stops'),
        ('regions', 'Regions and Cities'),
    ]
    
    export_type = models.CharField(
        max_length=20, 
        choices=EXPORT_TYPE_CHOICES, 
        unique=True,
        help_text="Type of cached export"
    )
    data = models.JSONField(
        help_text="Cached JSON data stored as JSONB in PostgreSQL"
    )
    last_updated = models.DateTimeField(auto_now=True)
    data_version = models.CharField(max_length=50)
    record_count = models.IntegerField(default=0)
    file_size_kb = models.IntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['export_type']),
            models.Index(fields=['last_updated']),
        ]
        verbose_name = "Cached Export"
        verbose_name_plural = "Cached Exports"
    
    def __str__(self):
        return f"{self.get_export_type_display()} - {self.data_version}" # type: ignore
    
    def update_metadata(self):
        """Calculate and update metadata after data change"""
        import json
        import sys
        
        # Calculate file size
        json_str = json.dumps(self.data)
        self.file_size_kb = sys.getsizeof(json_str) // 1024
        
        # Count records based on export type
        if self.export_type == 'complete':
            self.record_count = len(self.data.get('regions', []))
        elif self.export_type == 'terminals':
            self.record_count = len(self.data.get('terminals', []))
        elif self.export_type == 'routes':
            self.record_count = len(self.data.get('routes', []))
        elif self.export_type == 'regions':
            self.record_count = len(self.data.get('regions', []))
        
        self.save()

@receiver(post_save, sender=Terminal)
@receiver(post_save, sender=Route)
def auto_update_cache_on_verify(sender, instance, created, **kwargs):
    """Auto-update export cache when admin verifies terminal/route"""
    if instance.verified:
        cache_key = 'export_cache_update_cooldown'
        
        if cache.get(cache_key):
            logger.info(f"Cache update on cooldown, skipping for {sender.__name__} #{instance.id}")
            return
        
        cache.set(cache_key, True, 300)
        logger.info(f"Triggering cache update for verified {sender.__name__} #{instance.id}")
        
        def update_cache():
            try:
                call_command('update_export_cache')
                logger.info("Cache update completed successfully")
            except Exception as e:
                logger.error(f"Cache update failed: {str(e)}")
        
        Thread(target=update_cache, daemon=True).start()