import django_tables2 as tables

from .models import Template


class TemplateTable(tables.Table):
    class Meta:
        model = Template
        attrs = {"class": "table"}
        fields = ("name", "description")

    name = tables.Column()
