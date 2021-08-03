from apps.dashboards.serializers import DashboardSerializer
from rest_framework import generics

from .models import Dashboard


class DashboardSort(generics.UpdateAPIView):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
