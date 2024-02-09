import json

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, Q, When
from django.db.models.functions import Greatest
from django.forms.widgets import ChoiceWidget
from rest_framework.renderers import JSONRenderer

from .models import Table
from .serializers import TableSerializer


class TableSelect(ChoiceWidget):
    template_name = "django/forms/widgets/table_select.html"

    def __init__(self, attrs=None, choices=(), parent="workflow") -> None:
        super().__init__(attrs, choices)
        self.parent = parent
        self.parent_entity = None  # set in the form

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["parent_entity"] = self.parent_entity
        context["parent"] = self.parent

        tables = (
            Table.available.filter(project=self.parent_entity.project)
            .exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )
            .order_by("updated")
        )
        context["options"] = json.dumps(TableSerializer(tables, many=True).data)
        return context
