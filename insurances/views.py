from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from .serializers import BaseInsuredDataSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.core.exceptions import ValidationError


class InsuredDataView(APIView):
    """
    API endpoint to process insured person data.
    Uses a generic serializer with insurer-specific services.
    """
    @extend_schema(
        request=BaseInsuredDataSerializer,
        responses={
            201: BaseInsuredDataSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'object'},
                },
            },
        },
        description='Process insured data with insurer-specific field mappings based on case-insensitive insurer name. '
                    'Fields are dynamically validated based on the selected insurer service.',
        examples=[
            OpenApiExample(
                'Default Example',
                value={
                    'data': {
                        'insurer': 'generic',
                        'first_name': 'محمد',
                        'last_name': 'رضایی',
                        'phone_number': '09123456788',
                        'national_id': '1234567891',
                        'birth_date': '1990-01-01',
                        'insurer_id': 'GEN123',
                        'policyholder_name': 'فناپ',
                        'policyholder_id': 'FAN456',
                        'start_date': '2025-01-01',
                        'end_date': '2025-12-31',
                        'policy_id': 'POL790',
                        'plan_name': 'نقره‌ای',
                        'plan_id': 'PLN102',
                        'insured_id': 'INS203',
                    }
                },
                description='Valid payload for default service (unmatched insurer name, e.g., "generic"; uses model fields like first_name, email optional).'
            ),
            OpenApiExample(
                'Pasargad Example',
                value={
                    'data': {
                        'insurer': 'PASARGAD',
                        'first_name': 'علی',
                        'last_name': 'محمدی',
                        'email': 'ali@example.com',
                        'phone_number': '09123456789',
                        'national_id': '1234567890',
                        'birth_date': '1990-01-01',
                        'father_name': 'حسن',
                        'place_of_issue': 'تهران',
                        'insurer_id': 'INS001',
                        'policyholder_name': 'فناپ',
                        'policyholder_id': 'FAN456',
                        'start_date': '2025-01-01',
                        'end_date': '2025-12-31',
                        'policy_id': 'POL789',
                        'confirmation_date': '2025-01-02',
                        'plan_name': 'طلایی',
                        'plan_id': 'PLN101',
                        'insured_id': 'INS202',
                    }
                },
                description='Valid payload for Pasargad (insurer name: "pasargad" case-insensitive, requires first_name and email).'
            ),
            OpenApiExample(
                'Hekmat Example',
                value={
                    'data': {
                        'insurer': 'HEKMAT',
                        'name': 'رضا',
                        'family_name': 'رضایی',
                        'phone_number': '09123456788',
                        'national_id': '1234567891',
                        'birth_date': '1990-01-01',
                        'insurer_id': 'INS002',
                        'policyholder_name': 'فناپ',
                        'policyholder_id': 'FAN456',
                        'start_date': '2025-01-01',
                        'end_date': '2025-12-31',
                        'policy_id': 'POL790',
                        'plan_name': 'نقره‌ای',
                        'plan_id': 'PLN102',
                        'insured_id': 'INS203',
                    }
                },
                description='Valid payload for Hekmat (insurer name: "hekmat" case-insensitive, uses name/family_name, email optional).'
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        try:
            serializer = BaseInsuredDataSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': _('An unexpected error occurred: ') + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
