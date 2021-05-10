import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import Dashboard


class DashboardTable(tables.Table):
    class Meta:
        model = Dashboard
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
