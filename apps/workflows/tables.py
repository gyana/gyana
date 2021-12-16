import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

from apps.base.table import DuplicateColumn, NaturalDatetimeColumn

from .models import Workflow


class StatusColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object_name"] = "workflow"

        context["icon"] = record.state_icon
        context["text"] = record.state_text

        return get_template(self.template_name).render(context.flatten())


class WorkflowTable(tables.Table):
    class Meta:
        model = Workflow
        fields = ("name", "last_success_run", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    last_success_run = NaturalDatetimeColumn(
        accessor="last_success_run__started_at", verbose_name="Last successful run"
    )
    is_scheduled = tables.BooleanColumn(verbose_name="Scheduled")
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    # TODO: Fix orderable for status column.
    status = StatusColumn(template_name="columns/status.html", orderable=False)
    duplicate = DuplicateColumn(
        template_name="components/_duplicate.html",
        verbose_name="Actions",
        orderable=False,
    )
