from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Table
from .serializers import TableSerializer


class TableViewSet(viewsets.ModelViewSet):
    serializer_class = TableSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request is None:
            return Table.objects.none()
        return Table.objects.filter(project__team__members=self.request.user).all()
