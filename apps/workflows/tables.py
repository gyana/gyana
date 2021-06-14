import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import Node, Workflow


class WorkflowTable(tables.Table):
    class Meta:
        model = Workflow
        fields = ("name", "last_run", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    last_run = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    incomplete = tables.Column(empty_values=())

    def render_incomplete(self, value, record):
        return any((node.kind == Node.Kind.OUTPUT for node in record.nodes.iterator()))
