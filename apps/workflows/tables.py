import django_tables2 as tables
from apps.base.table import ICONS, DuplicateColumn, NaturalDatetimeColumn
from apps.nodes.models import Node
from django.template import Context
from django.template.loader import get_template

from .models import Workflow


class StatusColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object_name"] = "workflow"
        if record.failed:
            context["icon"] = ICONS["error"]
            context["text"] = "One of the nodes in this workflow failed."
        elif all((node.kind != Node.Kind.OUTPUT for node in record.nodes.iterator())):
            context["icon"] = ICONS["warning"]
            context["text"] = "Workflow has no output node and is incomplete."
        elif record.out_of_date:
            context["icon"] = ICONS["warning"]
            context["text"] = "Workflow has been updated since it's last run."
        else:
            context["icon"] = ICONS["success"]
            context["text"] = "Uptodate"

        return get_template(self.template_name).render(context.flatten())


class WorkflowTable(tables.Table):
    class Meta:
        model = Workflow
        fields = ("name", "last_run", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    last_run = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    status = StatusColumn(template_name="columns/status.html")
    duplicate = DuplicateColumn(
        template_name="components/_duplicate.html",
        verbose_name="Actions",
        orderable=False,
    )
