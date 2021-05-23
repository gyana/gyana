import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import Integration


class IntegrationTable(tables.Table):
    class Meta:
        model = Integration
        fields = ("name", "kind", "num_rows", "last_synced", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    last_synced = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()


class StructureTable(tables.Table):
    class Meta:
        fields = ("type", "name")
        attrs = {"class": "table"}

    type = tables.Column()
    name = tables.Column()
