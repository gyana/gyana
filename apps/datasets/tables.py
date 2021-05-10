import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import naturaltime

from .models import Dataset


class NaturalDatetimeColumn(tables.Column):
    def render(self, value):
        return naturaltime(value)


class DatasetTable(tables.Table):
    class Meta:
        model = Dataset
        fields = ("name", "kind", "last_synced", "created", "updated")

    name = tables.Column(linkify=True)
    last_synced = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
