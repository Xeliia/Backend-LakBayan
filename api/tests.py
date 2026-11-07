from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
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
)
from .serializers import RouteSerializer, serialize_fare_configuration


class SchemaUpgradeTests(TestCase):
	def test_legacy_records_load_without_new_optional_fields(self):
		region = Region.objects.create(name='Region')
		city = City.objects.create(name='City', region=region)
		mode = ModeOfTransport.objects.create(mode_name='bus', fare_type='fixed')
		terminal = Terminal.objects.create(
			name='Terminal',
			latitude=14,
			longitude=121,
			city=city,
			verified=False,
		)
		route = Route.objects.create(
			terminal=terminal,
			destination_name='Destination',
			mode=mode,
			verified=False,
		)
		stop = RouteStop.objects.create(
			route=route,
			stop_name='Stop',
			fare=Decimal('25.00'),
			order=1,
			latitude=14,
			longitude=121,
		)

		self.assertIsNone(terminal.station_id)
		self.assertIsNone(route.line_id)
		self.assertIsNone(route.fare_policy_id)
		self.assertIsNone(stop.station_id)
		self.assertIsNone(stop.distance_from_previous)
		self.assertIsNone(stop.time_from_previous)
		serialized_route = RouteSerializer(route).data
		self.assertIsNone(serialized_route['line_id'])
		self.assertIsNone(serialized_route['fare_policy'])
		self.assertEqual(serialized_route['stops'][0]['order'], 1)

	def test_fare_configuration_serializes_ordered_stations_and_products(self):
		regular = PassengerType.objects.create(code='regular')
		policy = FarePolicy.objects.create(
			policy_id='rail_regular',
			policy_type='matrix',
			media='stored_value',
			values=[[0, 20], [20, 0]],
		)
		FarePolicyStation.objects.create(policy=policy, station_id='station-a', order=1)
		FarePolicyStation.objects.create(policy=policy, station_id='station-b', order=2)
		policy.full_clean()

		product = FareProduct.objects.create(
			product_id='rail_regular_card',
			display_name='Regular Card',
			payment_method='stored_value',
			fare_policy=policy,
		)
		product.passenger_types.add(regular)

		data = serialize_fare_configuration()

		self.assertEqual(data['passenger_types']['regular']['discount']['type'], 'none')
		self.assertEqual(data['fare_products']['rail_regular_card']['passenger_types'], ['regular'])
		self.assertEqual(data['fare_policies']['rail_regular']['stations'], ['station-a', 'station-b'])
		self.assertEqual(data['fare_policies']['rail_regular']['values'], [[0, 20], [20, 0]])

	def test_matrix_policy_rejects_invalid_dimensions(self):
		policy = FarePolicy.objects.create(
			policy_id='invalid_matrix',
			policy_type='matrix',
			media='ticket',
			values=[[0, 20]],
		)
		FarePolicyStation.objects.create(policy=policy, station_id='station-a', order=1)
		FarePolicyStation.objects.create(policy=policy, station_id='station-b', order=2)

		with self.assertRaises(ValidationError):
			policy.full_clean()
