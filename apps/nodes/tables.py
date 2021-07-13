import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import Node


class NodeTable(tables.Table):
    class Meta:
        model = Node
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
