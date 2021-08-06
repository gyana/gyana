import django_tables2 as tables
from apps.base.table import NaturalDatetimeColumn

from .models import Sheet


class SheetTable(tables.Table):
    class Meta:
        model = Sheet
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
