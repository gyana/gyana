from django import template
from django.db.models.aggregates import Sum
from django.template import Context
from django.template.loader import get_template
from django.utils.html import format_html
from django_tables2 import Column, Table, TemplateColumn

from apps.base.table import NaturalDatetimeColumn

from .models import Integration


class ImageColumn(Column):
    def render(self, value):
        return format_html(
            '<img src="/static/{url}" class="fav" height="20px", width="20px">',
            url=value,
        )


class PendingStatusColumn(Column):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        instance = self.accessor.resolve(record) if self.accessor else record

        if instance is None:
            return

        context["icon"] = instance.state_icon
        context["text"] = instance.state_text

        # wrap status in turbo frame to fetch possible update
        if (
            instance.kind == Integration.Kind.CONNECTOR
            and instance.state == Integration.State.LOAD
        ):
            context["connector"] = instance.connector
            return get_template("connectors/icon.html").render(context.flatten())

        return get_template("columns/status.html").render(context.flatten())


class RowCountColumn(TemplateColumn):
    def __init__(self, **kwargs):
        verbose_name = kwargs.pop("verbose_name", "Rows")
        super().__init__(
            verbose_name=verbose_name,
            template_name="integrations/columns/num_rows.html",
            **kwargs
        )

    def order(self, queryset, is_descending):
        queryset = queryset.annotate(num_rows_agg=Sum("table__num_rows")).order_by(
            ("-" if is_descending else "") + "num_rows_agg"
        )
        return (queryset, True)


class IntegrationListTable(Table):
    class Meta:
        model = Integration
        # fields = ("name", "kind", "created_ready", "ready")
        fields = ()
        attrs = {"class": "table"}

    name = Column(linkify=True)
    icon = ImageColumn(accessor="icon", orderable=False)
    # TODO: Fix orderable on kind column.
    kind = Column(accessor="display_kind", orderable=False)
    state = PendingStatusColumn()
    num_rows = RowCountColumn()
    actions = TemplateColumn(template_name="integrations/columns/actions.html")
    # ready = BooleanColumn()
    # created_ready = NaturalDatetimeColumn(verbose_name="Added")
    # pending_deletion = NaturalDatetimeColumn(verbose_name="Expires")

    def order_num_rows(self, queryset, is_descending):
        queryset = queryset.annotate(num_rows_agg=Sum("table__num_rows")).order_by(
            ("-" if is_descending else "") + "num_rows_agg"
        )
        return (queryset, True)


class StructureTable(Table):
    class Meta:
        fields = ("name", "type")
        attrs = {"class": "table-data"}

    type = Column()
    name = Column()


class ReferencesTable(Table):
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
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
