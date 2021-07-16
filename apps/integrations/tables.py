from apps.utils.table import NaturalDatetimeColumn
from django.utils.safestring import mark_safe
from django_tables2 import Column, Table
from lib.icons import ICONS, icon_html

from .models import Integration


class IntegrationTable(Table):
    class Meta:
        model = Integration
        fields = (
            "name",
            "kind",
            "num_rows",
            "last_synced",
            "created",
            "updated",
        )
        attrs = {"class": "table"}

    name = Column(linkify=True)
    kind = Column(accessor="display_kind")
    last_synced = NaturalDatetimeColumn()
    status = Column(empty_values=())
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()

    def render_status(self, value, record):
        if record.last_synced is None:
            icon = ICONS["warning"]
            text = "Integration has not been synced yet."
        else:
            icon = ICONS["success"]
            text = "Synced and ready to be used."
        return mark_safe(icon_html.format(icon=icon, text=text))


class StructureTable(Table):
    class Meta:
        fields = ("name", "type")
        attrs = {"class": "table-data"}

    type = Column()
    name = Column()


class UsedInTable(Table):
    class Meta:
        model = Integration
        attrs = {"class": "table"}
        fields = (
            "name",
            "kind",
            "created",
            "updated",
        )

    name = Column(linkify=True)
