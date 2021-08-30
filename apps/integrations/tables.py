from apps.base.table import ICONS, NaturalDatetimeColumn
from django.template import Context
from django.template.loader import get_template
from django_tables2 import Column, Table

from .models import Integration

INTEGRATION_STATE_TO_ICON = {
    Integration.State.UPDATE: ICONS["warning"],
    Integration.State.LOAD: ICONS["loading"],
    Integration.State.ERROR: ICONS["error"],
    Integration.State.DONE: ICONS["warning"],
}

INTEGRATION_STATE_TO_MESSAGE = {
    Integration.State.UPDATE: "Incomplete setup",
    Integration.State.LOAD: "Importing",
    Integration.State.ERROR: "Error",
    Integration.State.DONE: "Ready to review",
}


class PendingStatusColumn(Column):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())

        if record.ready:
            context["icon"] = ICONS["success"]
            context["text"] = "Success"
        else:         
            context["icon"] = INTEGRATION_STATE_TO_ICON[record.state]
            context["text"] = INTEGRATION_STATE_TO_MESSAGE[record.state]

        # wrap status in turbo frame to fetch possible update
        if (
            record.kind == Integration.Kind.CONNECTOR
            and record.state == Integration.State.LOAD
        ):
            context["connector"] = record.connector
            return get_template("connectors/status.html").render(context.flatten())

        return get_template("columns/status.html").render(context.flatten())


class IntegrationListTable(Table):
    class Meta:
        model = Integration
        fields = ("name", "kind", "created_ready")
        attrs = {"class": "table"}

    name = Column(linkify=True)
    num_rows = Column(verbose_name="Rows")
    kind = Column(accessor="display_kind")
    created_ready = NaturalDatetimeColumn(verbose_name="Added")


class IntegrationPendingTable(Table):
    class Meta:
        model = Integration
        fields = (
            "name",
            "kind",
            "num_rows",
            "created",
        )
        attrs = {"class": "table"}

    name = Column(linkify=True)
    num_rows = Column(verbose_name="Rows")
    kind = Column(accessor="display_kind")
    created = NaturalDatetimeColumn(verbose_name="Started")
    state = PendingStatusColumn()


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
