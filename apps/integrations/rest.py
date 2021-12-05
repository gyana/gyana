from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Integration
from .serializers import IntegrationSerializer


class IntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = IntegrationSerializer
    filterset_fields = ["project"]
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request is None:
            return Integration.objects.none()
        return (
            Integration.objects.ready()
            .filter(project__team__in=self.request.user.teams.all())
            .all()
        )
