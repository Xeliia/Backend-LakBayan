import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import FarePolicy, FarePolicyStation, FareProduct, PassengerType


class Command(BaseCommand):
    help = 'Import strict passenger, fare product, and fare policy configuration from JSON'

    allowed_top_level_fields = {
        'last_updated', 'total_routes', 'total_terminals', 'export_timestamp',
        'format_version', 'currency', 'passenger_types', 'fare_products',
        'fare_policies',
    }
    matrix_fields = {'type', 'media', 'passenger_type', 'stations', 'values'}
    distance_fields = {
        'type', 'base_fare', 'base_distance_km', 'increment_fare',
        'increment_distance_km', 'maximum_fare', 'rounding', 'description',
    }

    def add_arguments(self, parser):
        parser.add_argument('source', type=Path, help='Path to the fare configuration JSON or fragment')
        parser.add_argument('--dry-run', action='store_true', help='Validate without writing database records')

    def handle(self, *args, **options):
        source = options['source']
        data = self.load_source(source)
        self.validate_document(data)

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('Fare configuration is valid. Dry run made no changes.'))
            return

        with transaction.atomic():
            passenger_types = self.import_passenger_types(data['passenger_types'])
            policies = self.import_policies(data['fare_policies'], passenger_types)
            self.import_products(data['fare_products'], passenger_types, policies)

        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(passenger_types)} passenger types, "
            f"{len(policies)} fare policies, and {len(data['fare_products'])} fare products."
        ))

    def load_source(self, source):
        try:
            raw = source.read_text(encoding='utf-8').strip()
            if not raw.startswith('{'):
                raw = '{' + raw
            return json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CommandError(f'Could not parse fare configuration: {error}') from error

    def validate_document(self, data):
        unknown = set(data) - self.allowed_top_level_fields
        if unknown:
            raise CommandError(f'Unsupported top-level fields: {sorted(unknown)}')
        required = {'passenger_types', 'fare_products', 'fare_policies'}
        missing = required - set(data)
        if missing:
            raise CommandError(f'Missing required top-level fields: {sorted(missing)}')
        if not isinstance(data['passenger_types'], dict):
            raise CommandError('passenger_types must be an object')
        if not isinstance(data['fare_products'], dict):
            raise CommandError('fare_products must be an object')
        if not isinstance(data['fare_policies'], dict):
            raise CommandError('fare_policies must be an object')

        for code, value in data['passenger_types'].items():
            if set(value) != {'discount'} or set(value['discount']) != {'type', 'value'}:
                raise CommandError(f'Invalid passenger type structure: {code}')
            if value['discount']['type'] not in {'none', 'percentage'}:
                raise CommandError(f'Unsupported discount type for {code}')
            if code == 'senior' and Decimal(str(value['discount']['value'])) != Decimal('50'):
                raise CommandError('Senior passenger type must have a 50 percent discount.')

        for product_id, value in data['fare_products'].items():
            if set(value) != {'display_name', 'payment_method', 'passenger_types', 'fare_policy'}:
                raise CommandError(f'Invalid fare product structure: {product_id}')
            if not isinstance(value['passenger_types'], list):
                raise CommandError(f'passenger_types must be a list for {product_id}')

        for policy_id, value in data['fare_policies'].items():
            self.validate_policy(policy_id, value)

        senior_product = data['fare_products'].get('lrt1_beep_senior')
        if senior_product and 'lrt1_beep_senior' not in data['fare_policies']:
            student = data['fare_policies'].get('lrt1_beep_student')
            if not student or student.get('type') != 'matrix':
                raise CommandError('Senior product requires a student matrix to copy.')

    def validate_policy(self, policy_id, value):
        policy_type = value.get('type')
        if policy_type == 'matrix':
            required_fields = {'type', 'media', 'stations', 'values'}
            if not required_fields.issubset(value) or not set(value).issubset(self.matrix_fields):
                raise CommandError(f'Invalid matrix policy fields: {policy_id}')
            stations = value['stations']
            matrix = value['values']
            if not isinstance(stations, list) or not stations:
                raise CommandError(f'Matrix stations must be a non-empty list: {policy_id}')
            if len(matrix) != len(stations) or any(len(row) != len(stations) for row in matrix):
                raise CommandError(f'Matrix dimensions do not match stations: {policy_id}')
            if any(isinstance(cell, bool) or not isinstance(cell, (int, float)) for row in matrix for cell in row):
                raise CommandError(f'Matrix values must be numeric: {policy_id}')
        elif policy_type == 'distance_based':
            if not self.distance_fields.issuperset(value) or 'type' not in value:
                raise CommandError(f'Invalid distance policy fields: {policy_id}')
            if value['rounding'] != 'whole':
                raise CommandError(f'Distance policy must use whole rounding: {policy_id}')
        else:
            raise CommandError(f'Unsupported fare policy type: {policy_id}')

    def import_passenger_types(self, definitions):
        result = {}
        for code, definition in definitions.items():
            discount = definition['discount']
            passenger_type, _ = PassengerType.objects.update_or_create(
                code=code,
                defaults={
                    'discount_type': discount['type'],
                    'discount_value': Decimal(str(discount['value'])),
                },
            )
            passenger_type.full_clean()
            result[code] = passenger_type
        return result

    def import_policies(self, definitions, passenger_types):
        definitions = dict(definitions)
        if 'lrt1_beep_senior' not in definitions and 'lrt1_beep_student' in definitions:
            student = definitions['lrt1_beep_student']
            definitions['lrt1_beep_senior'] = {
                **student,
                'passenger_type': 'senior',
            }

        result = {}
        for policy_id, definition in definitions.items():
            policy_type = definition['type']
            defaults = {
                'policy_type': policy_type,
                'media': definition.get('media', ''),
                'passenger_type': passenger_types.get(definition.get('passenger_type')),
                'values': definition.get('values', []),
                'base_fare': definition.get('base_fare'),
                'base_distance_km': definition.get('base_distance_km'),
                'increment_fare': definition.get('increment_fare'),
                'increment_distance_km': definition.get('increment_distance_km'),
                'maximum_fare': definition.get('maximum_fare'),
                'rounding': definition.get('rounding'),
                'description': definition.get('description', ''),
            }
            policy, _ = FarePolicy.objects.update_or_create(policy_id=policy_id, defaults=defaults)
            if policy_type == 'matrix':
                FarePolicyStation.objects.filter(policy=policy).delete()
                for order, station_id in enumerate(definition['stations']):
                    FarePolicyStation.objects.create(policy=policy, station_id=station_id, order=order + 1)
            policy.full_clean()
            result[policy_id] = policy
        return result

    def import_products(self, definitions, passenger_types, policies):
        for product_id, definition in definitions.items():
            policy_id = definition['fare_policy']
            if policy_id not in policies:
                raise CommandError(f'Unknown fare policy for product {product_id}: {policy_id}')
            product, _ = FareProduct.objects.update_or_create(
                product_id=product_id,
                defaults={
                    'display_name': definition['display_name'],
                    'payment_method': definition['payment_method'],
                    'fare_policy': policies[policy_id],
                },
            )
            try:
                product.passenger_types.set([passenger_types[code] for code in definition['passenger_types']])
            except KeyError as error:
                raise CommandError(f'Unknown passenger type for product {product_id}: {error.args[0]}') from error
