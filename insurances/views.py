from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from .serializers import BaseInsuredDataSerializer
from drf_spectacular.utils import extend_schema
from django.core.exceptions import ValidationError


class InsuredDataView(APIView):
    """
    API endpoint to process insured person data.
    Uses a generic serializer for all insurers.
    """
    @extend_schema(
        request=BaseInsuredDataSerializer
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
