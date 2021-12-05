from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Connector
from .serializers import ConnectorSerializer


class ConnectorViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectorSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request is None:
            return Connector.objects.none()
        return Connector.objects.filter(
            integration__project__team__members=self.request.user
        ).all()
