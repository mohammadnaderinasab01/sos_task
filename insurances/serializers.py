from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Insured, Insurer, Policyholder, Policy, Plan, InsuredStatus
from .services import BaseInsurerService, DefaultInsurerService, PasargadInsurerService, HekmatInsurerService


class BaseInsuredDataSerializer(serializers.Serializer):
    """
    Generic serializer for all insurers.
    Defines fixed keys, with mandatory fields enforced by service.
    """
    # Mandatory fields (minimal set)
    insurer = serializers.CharField(max_length=100, required=True, write_only=True)
    first_name = serializers.CharField(max_length=100, required=True, write_only=True)
    last_name = serializers.CharField(max_length=100, required=True, write_only=True)
    phone_number = serializers.CharField(max_length=11, required=True, write_only=True)
    national_id = serializers.CharField(max_length=10, required=True, write_only=True)
    birth_date = serializers.DateField(required=True, write_only=True)
    insurer_id = serializers.CharField(max_length=50, required=True, write_only=True)
    policyholder_name = serializers.CharField(max_length=100, required=True, write_only=True)
    policyholder_id = serializers.CharField(max_length=50, required=True, write_only=True)
    start_date = serializers.DateField(required=True, write_only=True)
    end_date = serializers.DateField(required=True, write_only=True)
    policy_id = serializers.CharField(max_length=50, required=True, write_only=True)
    plan_name = serializers.CharField(max_length=100, required=True, write_only=True)
    plan_id = serializers.CharField(max_length=50, required=True, write_only=True)
    insured_id = serializers.CharField(max_length=50, required=True, write_only=True)

    # Optional fields
    email = serializers.EmailField(required=False, allow_blank=True, write_only=True)
    father_name = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    place_of_issue = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    confirmation_date = serializers.DateField(required=False, allow_null=True, write_only=True)

    # Response fields
    personal_details = serializers.SerializerMethodField(read_only=True)
    insurer_response = serializers.SerializerMethodField(read_only=True)
    policyholder_response = serializers.SerializerMethodField(read_only=True)
    policy_response = serializers.SerializerMethodField(read_only=True)
    plan_response = serializers.SerializerMethodField(read_only=True)
    insured_status_response = serializers.SerializerMethodField(read_only=True)

    def validate_phone_number(self, value):
        """Validate Iranian mobile number format (09xxxxxxxxx)."""
        import re
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError(_('Enter a valid Iranian mobile number.'))
        return value

    def validate_national_id(self, value):
        """Ensure national_id is 10 digits."""
        import re
        if not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError(_('National ID must be exactly 10 digits.'))
        return value

    def validate_policy_id(self, value):
        """Ensure policy_id is unique."""
        if Policy.objects.filter(unique_id=value).exists():
            raise serializers.ValidationError(_('A policy with this ID already exists.'))
        return value

    def validate_plan_id(self, value):
        """Ensure plan_id is unique."""
        if Plan.objects.filter(unique_id=value).exists():
            raise serializers.ValidationError(_('A plan with this ID already exists.'))
        return value

    def validate_insured_id(self, value):
        """Ensure insured_id is unique."""
        if InsuredStatus.objects.filter(unique_id=value).exists():
            raise serializers.ValidationError(_('An insured status with this ID already exists.'))
        return value

    def validate(self, data):
        """Additional validation."""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(_('Policy start date must be before end date.'))
        if data.get('confirmation_date') and data['confirmation_date'] < data['start_date']:
            raise serializers.ValidationError(_('Confirmation date cannot be before start date.'))
        return data

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
        """Use appropriate insurer service based on insurer name."""
        insurer = validated_data.get('insurer', '')
        service_class = self.get_insurer_service(insurer)
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
