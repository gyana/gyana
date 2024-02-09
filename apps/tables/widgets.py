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

        table_pks = self.parent_entity.input_tables_fk
        context["used_in"] = table_pks

        queryset = (
            Table.available.filter(project=self.parent_entity.project)
            .exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )
            .order_by("updated")
        )

        tables = list(queryset.filter(pk__in=table_pks)) + list(
            queryset.exclude(pk__in=table_pks)[:5]
        )

        context["options"] = (
            JSONRenderer()
            .render(TableSerializer(tables, many=True).data)
            .decode("utf-8")
        )

        return context
