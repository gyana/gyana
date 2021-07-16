import django_tables2 as tables
from apps.utils.table import NaturalDatetimeColumn
from django.utils.safestring import mark_safe
from lib.icons import ICONS, icon_html

from .models import Dashboard


class DashboardTable(tables.Table):
    class Meta:
        model = Dashboard
        fields = ("name", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(linkify=True)
    status = tables.Column(empty_values=())
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()

    def render_status(self, value, record):
        if any(not widget.is_valid for widget in record.widget_set.iterator()):
            icon = ICONS["warning"]
            text = "This dashboard contains at least one incomplete widget."
        else:
            icon = ICONS["success"]
            text = "This dashboard is ready to be viewed."
        return mark_safe(icon_html.format(icon=icon, text=text))
