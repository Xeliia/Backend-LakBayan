from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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

    mode_name = models.CharField(max_length=20, choices=MODE_CHOICES, unique=True)
    fare_type = models.CharField(max_length=20, choices=FARE_TYPE_CHOICES)

    def __str__(self):
        return self.get_mode_name_display() # type: ignore

# Route Table
class Route(models.Model):
    terminal = models.ForeignKey('Terminal', on_delete=models.CASCADE, related_name='origin_routes')
    mode = models.ForeignKey('ModeOfTransport', on_delete=models.CASCADE, related_name='routes')
    verified = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='added_routes'
    )
    description = models.TextField(blank=True, null=True)
    polyline = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.mode.get_mode_name_display()} from {self.terminal.name or f'Terminal {self.terminal.id}'}"

# Route Stop Tables
class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=200)
    terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, blank=True, related_name='route_stops')
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    
    def __str__(self):
        return f"{self.stop_name} - {self.route}"