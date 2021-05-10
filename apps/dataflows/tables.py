import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import Dataflow


class DataflowTable(tables.Table):
    class Meta:
        model = Dataflow
        fields = ("name", "last_run", "created", "updated")

    name = tables.Column(linkify=True)
    last_run = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
