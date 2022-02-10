import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template
from django.utils.html import format_html

from apps.base.tables import DuplicateColumn, FaBooleanColumn, NaturalDatetimeColumn

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
        sequence = (
            "name",
            "status",
            "is_scheduled",
            "last_success_run",
            "created",
            "updated",
            "duplicate",
        )
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    last_success_run = NaturalDatetimeColumn(
        accessor="last_success_run__started_at", verbose_name="Last successful run"
    )
    is_scheduled = FaBooleanColumn(verbose_name="Scheduled")
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    # TODO: Fix orderable for status column.
    status = StatusColumn(template_name="columns/status.html", orderable=False)
    duplicate = DuplicateColumn(
        template_name="components/_duplicate.html",
        verbose_name="Actions",
        orderable=False,
    )


class ReferenceTable(tables.Table):
    class Meta:
        model = Workflow
        fields = ("name", "used_output_node", "kind", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(empty_values=())
    kind = tables.Column(accessor="parent_kind")
    used_output_node = tables.Column(empty_values=())
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()

    def render_name(self, record):
        if record.parent_kind == "Workflow":
            return format_html(
                f"<a target='_top' href={record.workflow.get_absolute_url()}>{record.workflow.name}</a>"
            )
        return format_html(
            f"<a target='_top' href={record.page.dashboard.get_absolute_url()}>{record.page.dashboard.name}</a>"
        )

    def render_used_output_node(self, record):
        if record.parent_kind == "Workflow":
            output_node = record.input_table.workflow_node
            return format_html(
                f"<a target='_top' href={output_node.get_absolute_url()}>{output_node.name}</a>"
            )
        output_node = record.table.workflow_node
        return format_html(
            f"<a target='_top' href={output_node.get_absolute_url()}>{output_node.name}</a>"
        )

    def render_updated(self, record):
        if record.parent_kind == "Workflow":
            return record.workflow.updated
        return record.page.dashboard.updated

    def render_created(self, record):
        if record.parent_kind == "Workflow":
            return record.workflow.created
        return record.page.dashboard.created
