import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

from apps.base.table import NaturalDatetimeColumn

from .models import GraphRun, JobRun


class RunStateColumn(tables.Column):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())

        context["icon"] = record.state_icon
        context["text"] = record.state_text

        return get_template("columns/status.html").render(context.flatten())


class JobRunTable(tables.Table):
    class Meta:
        model = JobRun
        attrs = {"class": "table"}
        fields = ("started_at", "duration", "state")

    started_at = NaturalDatetimeColumn(verbose_name="Started")
    state = RunStateColumn(verbose_name="Status")


class GraphRunTable(tables.Table):
    class Meta:
        model = GraphRun
        attrs = {"class": "table"}
        fields = ("started_at", "duration", "state")

    started_at = NaturalDatetimeColumn(verbose_name="Started")
    state = RunStateColumn(verbose_name="Status")
