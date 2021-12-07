import django_tables2 as tables
from apps.base.table import NaturalDatetimeColumn

from .models import Run


class RunTable(tables.Table):
    class Meta:
        model = Run
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
