from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

from django.core.exceptions import ValidationError

from api.models import FarePolicy, PassengerType


def calculate_distance_fare(
    policy: FarePolicy,
    distance_km: Decimal,
    passenger_type: PassengerType | None = None,
) -> Decimal:
    """Calculate a distance fare using the policy's explicit rounding rules.

    The passenger discount applies only to the base fare. Additional started
    kilometers are charged at the full increment fare without another discount.
    """
    if policy.policy_type != 'distance_based':
        raise ValidationError('The selected fare policy is not distance-based.')
    if distance_km < 0:
        raise ValidationError('Distance cannot be negative.')

    selected_passenger_type = passenger_type or policy.passenger_type
    discount = Decimal('0')
    if selected_passenger_type and selected_passenger_type.discount_type == 'percentage':
        discount = selected_passenger_type.discount_value / Decimal('100')

    discounted_base = policy.base_fare * (Decimal('1') - discount)
    if policy.rounding == 'whole':
        base_fare = discounted_base.quantize(Decimal('1'), rounding=ROUND_FLOOR)
    else:
        raise ValidationError('Unsupported distance fare rounding rule.')

    additional_distance = max(Decimal('0'), distance_km - policy.base_distance_km)
    additional_km = additional_distance / policy.increment_distance_km
    increments = additional_km.to_integral_value(rounding=ROUND_CEILING)
    fare = base_fare + (increments * policy.increment_fare)

    if policy.maximum_fare is not None:
        fare = min(fare, policy.maximum_fare)

    return fare


def calculate_matrix_fare(
    policy: FarePolicy,
    origin_station_id: str,
    destination_station_id: str,
) -> Decimal:
    """Return the final fare from an ordered matrix without reapplying discounts."""
    if policy.policy_type != 'matrix':
        raise ValidationError('The selected fare policy is not matrix-based.')

    station_ids = list(policy.stations.order_by('order').values_list('station_id', flat=True))
    try:
        origin_index = station_ids.index(origin_station_id)
        destination_index = station_ids.index(destination_station_id)
    except ValueError as error:
        raise ValidationError('Origin and destination stations must belong to the fare policy.') from error

    try:
        return Decimal(str(policy.values[origin_index][destination_index]))
    except (IndexError, TypeError, ValueError) as error:
        raise ValidationError('Fare matrix dimensions or values are invalid.') from error
