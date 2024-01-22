from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, Q, When
from django.db.models.functions import Greatest

from apps.base.forms import BaseModelForm
from apps.tables.models import Table

from .models import Table


class TableForm(BaseModelForm):
    class Meta:
        model = Table
        fields = []


INPUT_SEARCH_THRESHOLD = 0.3


class IntegrationSearchMixin:
    def search_queryset(self, field, project, table_instance, used_ids):
        field.queryset = (
            Table.available.filter(project=project)
            .exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )
            .annotate(
                is_used_in=Case(
                    When(id__in=used_ids, then=True),
                    default=False,
                ),
            )
            .order_by("updated")
        )
        if search := self.data.get("search"):
            field.queryset = (
                field.queryset.annotate(
                    similarity=Greatest(
                        TrigramSimilarity("integration__name", search),
                        TrigramSimilarity("workflow_node__workflow__name", search),
                        TrigramSimilarity("bq_table", search),
                    )
                )
                .filter(
                    Q(similarity__gte=INPUT_SEARCH_THRESHOLD)
                    | Q(id=getattr(table_instance, "id", None))
                )
                .order_by("-similarity")
            )
