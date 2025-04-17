from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .models import Insured, Insurer, Policyholder, Policy, Plan, InsuredStatus
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError


class BaseInsurerService:
    """
    Generic service for processing insurer data.
    Handles persistence and enforces creation order.
    """
    # Fixed key mapping (matches serializer)
    key_mapping = {
        'insurer': 'insurer',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'email': 'email',
        'phone_number': 'phone_number',
        'national_id': 'national_id',
        'birth_date': 'birth_date',
        'father_name': 'father_name',
        'place_of_issue': 'place_of_issue',
        'insurer_id': 'insurer_id',
        'policyholder_name': 'policyholder_name',
        'policyholder_id': 'policyholder_id',
        'start_date': 'start_date',
        'end_date': 'end_date',
        'policy_id': 'policy_id',
        'confirmation_date': 'confirmation_date',
        'plan_name': 'plan_name',
        'plan_id': 'plan_id',
        'insured_id': 'insured_id',
    }

    # Mandatory fields
    mandatory_fields = {
        'insurer',
        'first_name',
        'last_name',
        'phone_number',
        'national_id',
        'birth_date',
        'insurer_id',
        'policyholder_name',
        'policyholder_id',
        'start_date',
        'end_date',
        'policy_id',
        'plan_name',
        'plan_id',
        'insured_id',
    }

    def __init__(self, data):
        self.data = data or {}
        self.mapped_data = self._map_keys(data)

    def _map_keys(self, data):
        """Map JSON keys to model fields."""
        mapped = {}
        for model_field, json_key in self.key_mapping.items():
            if json_key in data:
                mapped[model_field] = data[json_key]
            elif model_field in self.mandatory_fields:
                raise ValidationError(_(f"Missing required field: {json_key}"))
        return mapped

    @transaction.atomic
    def save(self):
        """
        Save data in strict order: Insured -> Insurer -> Policyholder -> Policy -> Plan -> InsuredStatus.
        Ensures all tables are populated.
        """
        try:
            # 1. Save Insured
            insured = self._save_insured()
            # 2. Save Insurer
            insurer = self._save_insurer()
            # 3. Save Policyholder
            policyholder = self._save_policyholder()
            # 4. Save Policy
            policy = self._save_policy(insured, insurer, policyholder)
            # 5. Save Plan
            plan = self._save_plan(policy)
            # 6. Save InsuredStatus
            insured_status = self._save_insured_status(policy)

            return {
                'insured': insured,
                'insurer': insurer,
                'policyholder': policyholder,
                'policy': policy,
                'plan': plan,
                'insured_status': insured_status
            }
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower():
                raise ValidationError(
                    _('A policy for this person, insurer, policyholder, and start date already exists.'))
            raise ValidationError(_(f"Database error: {str(e)}"))
        except Exception as e:
            raise ValidationError(_(f"Failed to save data: {str(e)}"))

    def _save_insured(self):
        """Save Insured data."""
        insured_data = {
            'first_name': self.mapped_data['first_name'],
            'last_name': self.mapped_data['last_name'],
            'phone_number': self.mapped_data['phone_number'],
            'national_id': self.mapped_data['national_id'],
            'birth_date': self.mapped_data['birth_date'],
        }
        optional_fields = ['email', 'father_name', 'place_of_issue']
        for field in optional_fields:
            if field in self.mapped_data:
                insured_data[field] = self.mapped_data[field]
        return Insured.objects.get_or_create(
            national_id=insured_data['national_id'],
            defaults=insured_data
        )[0]

    def _save_insurer(self):
        """Save Insurer data."""
        insurer_data = {
            'name': self.mapped_data['insurer'],
            'unique_id': self.mapped_data['insurer_id'],
        }
        return Insurer.objects.get_or_create(
            unique_id=insurer_data['unique_id'],
            defaults={'name': insurer_data['name']}
        )[0]

    def _save_policyholder(self):
        """Save Policyholder data."""
        policyholder_data = {
            'name': self.mapped_data['policyholder_name'],
            'unique_id': self.mapped_data['policyholder_id'],
        }
        return Policyholder.objects.get_or_create(
            unique_id=policyholder_data['unique_id'],
            defaults={'name': policyholder_data['name']}
        )[0]

    def _save_policy(self, insured, insurer, policyholder):
        """Save Policy data."""
        policy_data = {
            'unique_id': self.mapped_data['policy_id'],
            'insured': insured,
            'insurer': insurer,
            'policyholder': policyholder,
            'start_date': self.mapped_data['start_date'],
            'end_date': self.mapped_data['end_date'],
            'confirmation_date': self.mapped_data.get('confirmation_date'),
        }
        return Policy.objects.create(**policy_data)

    def _save_plan(self, policy):
        """Save Plan data."""
        plan_data = {
            'policy': policy,
            'name': self.mapped_data['plan_name'],
            'unique_id': self.mapped_data['plan_id'],
        }
        return Plan.objects.create(**plan_data)

    def _save_insured_status(self, policy):
        """Save InsuredStatus data."""
        insured_status_data = {
            'policy': policy,
            'unique_id': self.mapped_data['insured_id'],
        }
        return InsuredStatus.objects.create(**insured_status_data)
