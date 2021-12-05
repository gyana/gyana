from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Sheet
from .serializers import SheetSerializer


class SheetViewSet(viewsets.ModelViewSet):
    serializer_class = SheetSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request is None:
            return Sheet.objects.none()
        return Sheet.objects.filter(
            integration__project__team__members=self.request.user
        ).all()
