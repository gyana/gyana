import itertools

import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

from apps.base.tables import ICONS, NaturalDatetimeColumn, TemplateColumn

from .models import Dashboard, DashboardVersion


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
        fields = ("created",)
        attrs = {"class": "table"}
        order_by = ("created",)

    created = NaturalDatetimeColumn()
    version = tables.Column(empty_values=(), orderable=False)
    action = TemplateColumn(
        template_name="dashboards/_restore_cell.html", orderable=False
    )

    def render_version(self):
        self.row_counter = getattr(self, "row_counter", itertools.count())
        return next(self.row_counter) + 1
