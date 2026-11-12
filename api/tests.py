from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

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
from .serializers import FarePolicySerializer, RouteSerializer, serialize_fare_configuration
from .services.fares import calculate_distance_fare
from .admin import FarePolicyAdmin


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

	def test_distance_fare_floors_discounted_base_and_ceils_started_kilometers(self):
		student = PassengerType.objects.create(
			code='student',
			discount_type='percentage',
			discount_value=20,
		)
		policy = FarePolicy.objects.create(
			policy_id='distance_default',
			policy_type='distance_based',
			media='general',
			base_fare=17,
			base_distance_km=4,
			increment_fare=2,
			increment_distance_km=1,
			rounding='whole',
		)

		self.assertEqual(calculate_distance_fare(policy, Decimal('4'), student), Decimal('13'))
		self.assertEqual(calculate_distance_fare(policy, Decimal('4.01'), student), Decimal('15'))
		self.assertEqual(calculate_distance_fare(policy, Decimal('5.01'), student), Decimal('17'))

	def test_distance_fare_applies_maximum_after_increments(self):
		policy = FarePolicy.objects.create(
			policy_id='distance_capped',
			policy_type='distance_based',
			media='general',
			base_fare=14,
			base_distance_km=4,
			increment_fare=2,
			increment_distance_km=1,
			maximum_fare=18,
			rounding='whole',
		)

		self.assertEqual(calculate_distance_fare(policy, Decimal('10')), Decimal('18'))

	def test_distance_policy_export_contains_only_distance_fields(self):
		policy = FarePolicy.objects.create(
			policy_id='distance_export',
			policy_type='distance_based',
			media='general',
			base_fare=14,
			base_distance_km=4,
			increment_fare=2,
			increment_distance_km=1,
			rounding='whole',
		)

		serialized = FarePolicySerializer(policy).data

		self.assertIn('base_fare', serialized)
		self.assertNotIn('stations', serialized)
		self.assertNotIn('values', serialized)

	def test_route_contribution_rejects_policy_mode_mismatch(self):
		region = Region.objects.create(name='Region')
		city = City.objects.create(name='City', region=region)
		terminal = Terminal.objects.create(name='Terminal', latitude=14, longitude=121, city=city, verified=True)
		mode = ModeOfTransport.objects.create(mode_name='bus', fare_type='fixed')
		policy = FarePolicy.objects.create(
			policy_id='matrix_policy', policy_type='matrix', media='ticket', values=[]
		)

		from .serializers import RouteContributionSerializer
		serializer = RouteContributionSerializer(data={
			'terminal': terminal.id,
			'destination_name': 'Destination',
			'mode': mode.id,
			'fare_policy': policy.policy_id,
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('fare_policy', serializer.errors)

	def test_complete_export_contains_fare_configuration_and_nested_fields(self):
		passenger_type = PassengerType.objects.create(code='senior', discount_type='percentage', discount_value=20)
		policy = FarePolicy.objects.create(
			policy_id='distance_policy', policy_type='distance_based', media='general',
			base_fare=14, base_distance_km=4, increment_fare=2,
			increment_distance_km=1, rounding='whole',
		)
		product = FareProduct.objects.create(
			product_id='senior_product', display_name='Senior Product',
			payment_method='card', fare_policy=policy,
		)
		product.passenger_types.add(passenger_type)

		response = APIClient().get('/api/complete/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['passenger_types']['senior']['discount']['value'], 20.0)
		self.assertEqual(response.data['fare_products']['senior_product']['passenger_types'], ['senior'])
		self.assertEqual(response.data['fare_policies']['distance_policy']['rounding'], 'whole')
		self.assertNotIn('stations', response.data['fare_policies']['distance_policy'])

	def test_fare_changes_trigger_cache_refresh_for_model_and_many_to_many_changes(self):
		cache.delete('export_cache_update_cooldown')
		with patch('api.models.Thread') as thread:
			passenger_type = PassengerType.objects.create(code='regular')
			self.assertTrue(thread.called)
			thread.reset_mock()
			product = FareProduct.objects.create(
				product_id='regular_product', display_name='Regular Product', payment_method='cash'
			)
			cache.delete('export_cache_update_cooldown')
			product.passenger_types.add(passenger_type)
			self.assertTrue(thread.called)
			thread.return_value.start.assert_called()

	def test_admin_exposes_distance_policy_fields(self):
		fields = set(FarePolicyAdmin.fields)
		self.assertTrue({
			'base_fare', 'base_distance_km', 'increment_fare',
			'increment_distance_km', 'maximum_fare', 'rounding', 'description',
		}.issubset(fields))

	def test_matrix_policy_can_be_created_before_admin_inline_stations(self):
		policy = FarePolicy(
			policy_id='matrix_pending',
			policy_type='matrix',
			media='ticket',
			values=[[0]],
		)

		policy.full_clean()

	def test_senior_passenger_type_requires_fifty_percent_discount(self):
		passenger_type = PassengerType(code='senior', discount_type='percentage', discount_value=20)

		with self.assertRaises(ValidationError):
			passenger_type.full_clean()

	def test_corrected_configuration_import_creates_separate_senior_policy(self):
		source = settings.BASE_DIR / '.context' / 'example-new.txt'
		call_command('import_fare_configuration', str(source))

		senior = PassengerType.objects.get(code='senior')
		student_policy = FarePolicy.objects.get(policy_id='lrt1_beep_student')
		senior_policy = FarePolicy.objects.get(policy_id='lrt1_beep_senior')
		senior_product = FareProduct.objects.get(product_id='lrt1_beep_senior')

		self.assertEqual(senior.discount_value, Decimal('50.00'))
		self.assertNotEqual(student_policy.policy_id, senior_policy.policy_id)
		self.assertEqual(senior_policy.passenger_type, senior)
		self.assertEqual(senior_product.fare_policy, senior_policy)
		self.assertEqual(
			list(student_policy.stations.values_list('station_id', flat=True)),
			list(senior_policy.stations.values_list('station_id', flat=True)),
		)
		self.assertEqual(student_policy.values, senior_policy.values)
