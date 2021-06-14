import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn
from django.utils.safestring import mark_safe

from .models import Node, Workflow

ICONS = {
    "success": "fa-check-circle text-green",
    "error": "fa-times-hexagon text-red",
    "warning": "fa-exclamation-triangle text-orange",
}


class WorkflowTable(tables.Table):
    class Meta:
        model = Workflow
        fields = ("name", "last_run", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    last_run = NaturalDatetimeColumn()
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    status = tables.Column(empty_values=())

    def render_status(self, value, record):
        if record.failed:
            icon = ICONS["error"]
            text = "One of the nodes in this workflow failed."
        elif all((node.kind != Node.Kind.OUTPUT for node in record.nodes.iterator())):
            icon = ICONS["warning"]
            text = "Workflow has no output node and is incomplete."
        elif record.out_of_date:
            icon = ICONS["warning"]
            text = "Workflow has been updated since it's last run."

        else:
            icon = ICONS["success"]
            text = "Uptodate"

        return mark_safe(
            f"<div class='tooltip tooltip--bottom px-6'>"
            f"<i class='fa {icon}'></i>"
            f"<span class='tooltip__content'>{text}</span>"
            f"</div>"
        )
