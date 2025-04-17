from django.urls import path
from .views import InsuredDataView

urlpatterns = [
    path('insured-data/', InsuredDataView.as_view(), name='insured-data'),
]
