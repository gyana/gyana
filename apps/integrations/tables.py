import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import Integration


class IntegrationTable(tables.Table):
    class Meta:
        model = Integration
        fields = ("name", "kind", "last_synced", "created", "updated")

    name = tables.Column(linkify=True)
    last_synced = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
