import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

from apps.base.table import ICONS, DuplicateColumn, NaturalDatetimeColumn

from .models import Dashboard


class StatusColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object_name"] = "dashboard"
        if any(not widget.is_valid for widget in record.get_all_widgets()):
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
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    # TODO: Fix orderable on status column.
    status = StatusColumn(template_name="columns/status.html", orderable=False)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    duplicate = DuplicateColumn(
        template_name="components/_duplicate.html",
        orderable=False,
        verbose_name="Actions",
    )
