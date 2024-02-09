import django_filters
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.db.models.functions import Greatest
from django_filters import rest_framework as drf_filters

from .models import Table

INPUT_SEARCH_THRESHOLD = 0.3


class TableFilter(drf_filters.FilterSet):
    search = django_filters.CharFilter(field_name="search", method="filter_search")

    class Meta:
        model = Table
        fields = "__all__"

    def filter_search(self, queryset, name, value):
        return (
            queryset.annotate(
                similarity=Greatest(
                    TrigramSimilarity("integration__name", value),
                    TrigramSimilarity("workflow_node__workflow__name", value),
                    TrigramSimilarity("name", value),
                )
            )
            .filter(Q(similarity__gte=INPUT_SEARCH_THRESHOLD))
            .order_by("-similarity")
        )
