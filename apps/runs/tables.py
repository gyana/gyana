import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

from apps.base.table import NaturalDatetimeColumn

from .models import Run


class RunStateColumn(tables.Column):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())

        context["icon"] = record.state_icon
        context["text"] = record.state_text

        return get_template("columns/status.html").render(context.flatten())


class RunTable(tables.Table):
    class Meta:
        model = Run
        attrs = {"class": "table"}
        fields = ("created", "duration", "state")

    created = NaturalDatetimeColumn(verbose_name="Triggered")
    state = RunStateColumn(verbose_name='Status')
