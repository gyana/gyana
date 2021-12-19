import django_tables2 as tables
from apps.base.table import NaturalDatetimeColumn

from .models import OAuth2


class OAuth2Table(tables.Table):
    class Meta:
        model = OAuth2
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
