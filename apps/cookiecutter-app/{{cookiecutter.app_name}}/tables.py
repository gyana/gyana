import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn

from .models import {{ cookiecutter.model_name }}


class {{ cookiecutter.model_name }}Table(tables.Table):
    class Meta:
        model = {{ cookiecutter.model_name }}
        attrs = {"class": "table"}
        fields = ("name", "created", "updated")

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
