import itertools

import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

from apps.base.tables import ICONS, NaturalDatetimeColumn, TemplateColumn

from .models import Dashboard, DashboardUpdate, DashboardVersion


class StatusColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object_name"] = "dashboard"
        if any(not widget.is_valid for widget in record.widgets.all()):
            context["icon"] = ICONS["warning"]
            context["text"] = "This dashboard contains at least one incomplete widget."
        else:
            context["icon"] = ICONS["success"]
            context["text"] = "This dashboard is ready to be viewed."
        return get_template(self.template_name).render(context.flatten())


class DashboardTable(tables.Table):
    class Meta:
        model = Dashboard
        fields = ("name", "created", "updated")
        sequence = ("name", "status", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    # TODO: Fix orderable on status column.
    status = StatusColumn(template_name="columns/status.html", orderable=False)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    actions = TemplateColumn(
        template_name="components/_actions.html",
        orderable=False,
    )


class DashboardHistoryTable(tables.Table):
    class Meta:
        model = DashboardVersion
        fields = ("name", "created")
        attrs = {"class": "table"}
        order_by = ("-created",)

    created = NaturalDatetimeColumn()
    name = tables.Column(
        empty_values=(),
        orderable=False,
        attrs={"th": {"style": "min-width: 50%; width: 50%;"}},
    )
    action = TemplateColumn(
        template_name="dashboards/_restore_cell.html",
        orderable=False,
        extra_context={"href": "dashboards:restore"},
    )

    def render_name(self, record, table, **kwargs):
        self.row_counter = getattr(self, "row_counter", itertools.count())

        context = getattr(table, "context", Context())
        context["object"] = record
        context["placeholder"] = f"Version {next(self.row_counter)+1}"
        return get_template("dashboards/version_name.html").render(context.flatten())


class DashboardUpdateTable(tables.Table):
    class Meta:
        model = DashboardUpdate
        fields = ("created", "content_object")
        attrs = {"class": "table"}
        order_by = ("-created",)

    created = NaturalDatetimeColumn()
    content_object = tables.Column(
        verbose_name="Changed",
        linkify=lambda value: value.get_absolute_url() if value else None,
        orderable=False,
        attrs={"a": {"target": "_top"}},
        default="Deleted",
    )
    action = TemplateColumn(
        template_name="dashboards/_restore_cell.html",
        orderable=False,
        extra_context={"href": "dashboards:restore-update"},
    )
