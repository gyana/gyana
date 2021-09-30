import django_tables2 as tables
from apps.base.table import NaturalDatetimeColumn

from .models import CName


class CNameTable(tables.Table):
    class Meta:
        model = CName
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
