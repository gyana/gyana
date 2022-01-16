import django_tables2 as tables

from apps.base.tables import NaturalDatetimeColumn

from .models import CName


class CNameTable(tables.Table):
    class Meta:
        model = CName
        attrs = {"class": "table"}
        fields = ("domain", "created")

    domain = tables.Column()
    created = NaturalDatetimeColumn()
    # TODO: Fix orderable for status column.
    status = tables.TemplateColumn(template_name="cnames/_status.html", orderable=False)
    actions = tables.TemplateColumn(
        template_name="cnames/actions.html", verbose_name="Actions", orderable=False
    )
