from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Insured, Insurer, Policyholder, Policy, Plan, InsuredStatus
from .services import BaseInsurerService, DefaultInsurerService, PasargadInsurerService, HekmatInsurerService


class BaseInsuredDataSerializer(serializers.Serializer):
    """
    Generic serializer for all insurers.
    Accepts dynamic fields based on insurer-specific key mappings.
    Validates mandatory fields and transforms to model fields.
    """
    data = serializers.DictField(child=serializers.CharField(allow_blank=True), write_only=True)

    # Response fields
    personal_details = serializers.SerializerMethodField(read_only=True)
    insurer_response = serializers.SerializerMethodField(read_only=True)
    policyholder_response = serializers.SerializerMethodField(read_only=True)
    policy_response = serializers.SerializerMethodField(read_only=True)
    plan_response = serializers.SerializerMethodField(read_only=True)
    insured_status_response = serializers.SerializerMethodField(read_only=True)

    def validate_data(self, value):
        """Validate phone_number and national_id formats if present."""
        import re
        if 'phone_number' in value:
            if not re.match(r'^09\d{9}$', value['phone_number']):
                raise serializers.ValidationError(_('Enter a valid Iranian mobile number.'))
        if 'national_id' in value:
            if not re.match(r'^\d{10}$', value['national_id']):
                raise serializers.ValidationError(_('National ID must be exactly 10 digits.'))
        return value

    def validate(self, data):
        """Validate and transform payload based on insurer-specific service."""
        payload = data.get('data', {})
        insurer = payload.get('insurer', '')
        service_class = self.get_insurer_service(insurer)

        # Validate mandatory fields
        missing_fields = []
        for model_field in service_class.mandatory_fields:
            json_key = next((k for k, v in service_class.key_mapping.items() if v == model_field), None)
            if json_key and json_key not in payload:
                missing_fields.append(json_key)
        if missing_fields:
            raise serializers.ValidationError(_(f"Missing required fields: {', '.join(missing_fields)}"))

        # Transform payload to model field names
        transformed_data = {}
        for json_key, value in payload.items():
            # Find model field for the input key
            model_field = next((k for k, v in service_class.key_mapping.items() if v == json_key), json_key)
            transformed_data[model_field] = value

        # Additional validations
        if 'start_date' in transformed_data and 'end_date' in transformed_data:
            if transformed_data['start_date'] >= transformed_data['end_date']:
                raise serializers.ValidationError(_('Policy start date must be before end date.'))
        if 'confirmation_date' in transformed_data and 'start_date' in transformed_data:
            if transformed_data.get(
                'confirmation_date') and transformed_data['confirmation_date'] < transformed_data['start_date']:
                raise serializers.ValidationError(_('Confirmation date cannot be before start date.'))
        if 'policy_id' in transformed_data and Policy.objects.filter(unique_id=transformed_data['policy_id']).exists():
            raise serializers.ValidationError(_('A policy with this ID already exists.'))
        if 'plan_id' in transformed_data and Plan.objects.filter(unique_id=transformed_data['plan_id']).exists():
            raise serializers.ValidationError(_('A plan with this ID already exists.'))
        if 'insured_id' in transformed_data and InsuredStatus.objects.filter(
            unique_id=transformed_data['insured_id']).exists():
            raise serializers.ValidationError(_('An insured status with this ID already exists.'))

        return transformed_data

    def get_personal_details(self, obj):
        """Return full name for response."""
        return f"{obj['insured'].first_name} {obj['insured'].last_name}"

    def get_insurer_response(self, obj):
        """Return insurer name for response."""
        return obj['insurer'].name

    def get_policyholder_response(self, obj):
        """Return policyholder name for response."""
        return obj['policyholder'].name

    def get_policy_response(self, obj):
        """Return policy string for response."""
        return str(obj['policy'])

    def get_plan_response(self, obj):
        """Return plan name for response."""
        return obj['plan'].name

    def get_insured_status_response(self, obj):
        """Return insured status string for response."""
        return str(obj['insured_status'])

    def create(self, validated_data):
        """Use appropriate insurer service to save data."""
        service_class = self.get_insurer_service(validated_data.get('insurer', ''))
        service = service_class(validated_data)
        return service.save()

    def get_insurer_service(self, insurer):
        """Select insurer service based on case-insensitive insurer name."""
        services = [
            PasargadInsurerService,
            HekmatInsurerService,
            DefaultInsurerService,  # Default last to ensure specific names take precedence
        ]
        for service in services:
            if hasattr(service, 'insurer_name') and service.insurer_name:
                if insurer.lower() == service.insurer_name.lower():
                    return service
        return DefaultInsurerService  # Fallback for unmatched or empty insurer

    def to_representation(self, instance):
        """Customize response format."""
        return {
            'message': _('Data processed successfully'),
            'data': {
                'personal_details': self.get_personal_details(instance),
                'insurer': self.get_insurer_response(instance),
                'policyholder': self.get_policyholder_response(instance),
                'policy': self.get_policy_response(instance),
                'plan': self.get_plan_response(instance),
                'insured_status': self.get_insured_status_response(instance),
            }
        }
