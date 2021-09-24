import django_tables2 as tables

from apps.base.table import NaturalDatetimeColumn

from .models import CName


class CNameTable(tables.Table):
    class Meta:
        model = CName
        attrs = {"class": "table"}
        fields = ("domain", "created", "updated")

    domain = tables.Column()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()

    actions = tables.TemplateColumn(
        template_name="cnames/actions.html", verbose_name="Actions"
    )
