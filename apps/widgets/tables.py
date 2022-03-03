import django_tables2 as tables
from django.utils.html import format_html
from django_tables2.utils import A

from apps.base.tables import NaturalDatetimeColumn
from apps.widgets.models import Widget


class WidgetHistory(tables.Table):
    class Meta:
        model = Widget.history.model
        fields = (
            "history_date",
            "name",
            "page__position",
            "history_user__email",
            "history_type",
        )
        attrs = {"class": "table"}
        order_by = ("-history_date",)

    history_date = NaturalDatetimeColumn(verbose_name="Changed")
    name = tables.Column(empty_values=())
    page__position = tables.Column(
        verbose_name="Page", linkify=lambda record: record.page.get_absolute_url()
    )
    history_user__email = tables.LinkColumn(
        verbose_name="Changed by",
        viewname="team_members:update",
        args=(A("page__dashboard__project__team__id"), A("history_user_id")),
    )
    history_type = tables.Column(verbose_name="Change")

    def render_name(self, record):
        name = record.name or f"Untitled {record.get_kind_display()}"
        return format_html(
            f"<a target='_top' href='{record.instance.get_absolute_url()}'>{name}</a>"
        )
