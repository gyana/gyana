from apps.base.table import ICONS, NaturalDatetimeColumn
from django.template import Context
from django.template.loader import get_template
from django_tables2 import Column, Table, TemplateColumn

from .models import Integration


class StatusColumn(TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        if record.state == Integration.State.UPDATE:
            context["icon"] = ICONS["warning"]
            context["text"] = "Incomplete setup"
        if record.state == Integration.State.LOAD:
            context["icon"] = ICONS["loading"]
            context["text"] = "Importing"
        elif record.state == Integration.State.ERROR:
            context["icon"] = ICONS["error"]
            context["text"] = "Error"
        elif record.state == Integration.State.DONE:
            context["icon"] = ICONS["success"]
            context["text"] = "Ready to review"

        return get_template(self.template_name).render(context.flatten())


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
    state = StatusColumn(template_name="columns/status.html")


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
