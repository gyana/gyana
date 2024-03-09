from django_filters import rest_framework as drf_filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.tables.filters import TableFilter

from .models import Table
from .serializers import TableSerializer


class TableViewSet(viewsets.ModelViewSet):
    serializer_class = TableSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [drf_filters.DjangoFilterBackend]
    filterset_fields = ["project", "search"]
    filterset_class = TableFilter

    def get_queryset(self):
        if self.request is None:
            return Table.objects.none()

        return Table.available.exclude(
            source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
        )
