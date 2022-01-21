import django_tables2 as tables

from apps.base.tables import NaturalDatetimeColumn

from .models import Node


class ReferencesTable(tables.Table):
    class Meta:
        model = Node
        attrs = {"class": "table"}
        fields = (
            "name",
            "kind",
            "created",
            "updated",
        )

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
