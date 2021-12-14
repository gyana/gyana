from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Dashboard
from .serializers import DashboardSerializer


class DashboardViewSet(viewsets.ModelViewSet):
    serializer_class = DashboardSerializer
    filterset_fields = ["project"]
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request is None:
            return Dashboard.objects.none()
        return Dashboard.objects.filter(project__team__members=self.request.user).all()
