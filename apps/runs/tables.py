import django_tables2 as tables

from apps.base.table import NaturalDatetimeColumn

from .models import Run


class RunTable(tables.Table):
    class Meta:
        model = Run
        attrs = {"class": "table"}
        fields = ("created",)

    created = NaturalDatetimeColumn(verbose_name="Started")
    completed = NaturalDatetimeColumn(accessor="result__date_done")
    status = NaturalDatetimeColumn(accessor="result__status")
