from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from threading import Thread
from decimal import Decimal
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
    station_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
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
        ('matrix', 'Matrix'),
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
    line_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    direction = models.CharField(max_length=100, blank=True, null=True)
    mode = models.ForeignKey('ModeOfTransport', on_delete=models.CASCADE, related_name='routes')
    fare_policy = models.ForeignKey(
        'FarePolicy',
        on_delete=models.SET_NULL,
        related_name='routes',
        blank=True,
        null=True,
        to_field='policy_id',
    )
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
    station_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, blank=True, related_name='route_stops')
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    distance_from_previous = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time = models.IntegerField(null=True, blank=True)
    time_from_previous = models.IntegerField(null=True, blank=True)
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


class PassengerType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=20,
        choices=[('none', 'None'), ('percentage', 'Percentage')],
        default='none',
    )
    discount_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    def clean(self):
        super().clean()
        if self.discount_type == 'none' and self.discount_value != 0:
            raise ValidationError("A passenger type with no discount must have a value of 0.")

    def __str__(self):
        return self.code


class FarePolicy(models.Model):
    POLICY_TYPE_CHOICES = [
        ('fixed', 'Fixed'),
        ('distance_based', 'Distance Based'),
        ('matrix', 'Matrix'),
    ]

    policy_id = models.CharField(max_length=100, primary_key=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    media = models.CharField(max_length=100)
    passenger_type = models.ForeignKey(
        PassengerType,
        on_delete=models.SET_NULL,
        related_name='fare_policies',
        blank=True,
        null=True,
    )
    values = models.JSONField(default=list, blank=True)

    def clean(self):
        super().clean()
        if self.policy_type != 'matrix':
            return

        stations = list(self.stations.values_list('station_id', flat=True)) if self.pk else []  # type: ignore[attr-defined]
        matrix = self.values
        if not isinstance(matrix, list) or len(matrix) != len(stations):
            raise ValidationError("A matrix fare policy must have one row per station.")
        if any(not isinstance(row, list) or len(row) != len(stations) for row in matrix):
            raise ValidationError("A matrix fare policy must have one value per station in every row.")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for row in matrix for value in row):
            raise ValidationError("Matrix fare values must be numeric.")

    def __str__(self):
        return self.policy_id


class FarePolicyStation(models.Model):
    policy = models.ForeignKey(FarePolicy, on_delete=models.CASCADE, related_name='stations')
    station_id = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['policy', 'station_id'], name='unique_policy_station'),
            models.UniqueConstraint(fields=['policy', 'order'], name='unique_policy_station_order'),
        ]

    def __str__(self):
        return f"{self.policy.policy_id}: {self.station_id}"


class FareProduct(models.Model):
    product_id = models.CharField(max_length=100, primary_key=True)
    display_name = models.CharField(max_length=200)
    payment_method = models.CharField(max_length=100)
    passenger_types = models.ManyToManyField(PassengerType, related_name='fare_products', blank=True)
    fare_policy = models.ForeignKey(
        FarePolicy,
        on_delete=models.SET_NULL,
        related_name='fare_products',
        blank=True,
        null=True,
        to_field='policy_id',
    )

    def __str__(self):
        return self.product_id
    
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

# Lakbay Points (LP) System
class GenderChoices(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    PREFER_NOT_TO_SAY = 'prefer not to say', 'Prefer not to say'

class UserProfile(models.Model):
    """Extended user profile for Lakbay Points"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    lakbay_points = models.IntegerField(default=0)
    gender = models.CharField(
        max_length=18,
        choices=GenderChoices.choices,
        default=GenderChoices.PREFER_NOT_TO_SAY,
    )
    
    def __str__(self):
        return f"{self.user.username}'s Profile - {self.lakbay_points} LP"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# Track verification status to award LP only on first verification
_terminal_verified_cache = {}
_route_verified_cache = {}

@receiver(post_save, sender=Terminal)
def award_lp_on_terminal_verify(sender, instance, created, **kwargs):
    """Award 20-80 random LP when admin verifies a terminal"""
    import random
    
    if created:
        # Store initial state for new terminals
        _terminal_verified_cache[instance.id] = instance.verified
        return
    
    # Check if verified changed from False to True
    was_verified = _terminal_verified_cache.get(instance.id, False)
    _terminal_verified_cache[instance.id] = instance.verified
    
    if instance.verified and not was_verified and instance.added_by:
        # Ensure user has a profile
        profile, _ = UserProfile.objects.get_or_create(user=instance.added_by)
        points = random.randint(20, 80)
        profile.lakbay_points += points
        profile.save()
        logger.info(f"Awarded {points} LP to {instance.added_by.username} for verified terminal #{instance.id}")


@receiver(post_save, sender=Route)
def award_lp_on_route_verify(sender, instance, created, **kwargs):
    """Award 20-80 random LP when admin verifies a route"""
    import random
    
    if created:
        # Store initial state for new routes
        _route_verified_cache[instance.id] = instance.verified
        return
    
    # Check if verified changed from False to True
    was_verified = _route_verified_cache.get(instance.id, False)
    _route_verified_cache[instance.id] = instance.verified
    
    if instance.verified and not was_verified and instance.added_by:
        # Ensure user has a profile
        profile, _ = UserProfile.objects.get_or_create(user=instance.added_by)
        points = random.randint(20, 80)
        profile.lakbay_points += points
        profile.save()
        logger.info(f"Awarded {points} LP to {instance.added_by.username} for verified route #{instance.id}")