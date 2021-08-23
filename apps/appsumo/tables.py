import django_tables2 as tables
from apps.base.table import NaturalDatetimeColumn

from .models import AppsumoCode


class AppsumoCodeTable(tables.Table):
    class Meta:
        model = AppsumoCode
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
