from apps.utils.table import ICONS, NaturalDatetimeColumn
from django.template import Context
from django.template.loader import get_template
from django_tables2 import Column, Table, TemplateColumn

from .models import Integration


class StatusColumn(TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        if record.last_synced is None:
            context["icon"] = ICONS["warning"]
            context["text"] = "Integration has not been synced yet."
        else:
            context["icon"] = ICONS["success"]
            context["text"] = "Synced and ready to be used."

        return get_template(self.template_name).render(context.flatten())


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
    status = StatusColumn(template_name="columns/status.html")
    created = StatusColumn(template_name="columns/status.html")
    updated = NaturalDatetimeColumn()


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
