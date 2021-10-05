import django_tables2 as tables

from apps.base.table import NaturalDatetimeColumn

from .models import CName


class CNameTable(tables.Table):
    class Meta:
        model = CName
        attrs = {"class": "table"}
        fields = ("domain", "created")

    domain = tables.Column()
    created = NaturalDatetimeColumn()
    status = tables.TemplateColumn(template_name="cnames/_status.html")
    actions = tables.TemplateColumn(
        template_name="cnames/actions.html", verbose_name="Actions"
    )
