import django_tables2 as tables
from django.db.models.aggregates import Sum
from django.template import Context
from django.template.loader import get_template

from apps.base.table import NaturalDatetimeColumn, NaturalDayColumn

from .models import Integration


class PendingStatusColumn(tables.Column):
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


class RowCountColumn(tables.TemplateColumn):
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


class IntegrationListTable(tables.Table):
    class Meta:
        model = Integration
        fields = ()
        attrs = {"class": "table"}

    icon = tables.TemplateColumn(
        template_name="columns/image.html",
        orderable=False,
        verbose_name="",
        attrs={"th": {"style": "min-width: auto; width: 0%;"}},
    )
    name = tables.Column(linkify=True)
    kind = tables.Column(
        accessor="display_kind",
        orderable=False,
        verbose_name="Kind",
        attrs={"th": {"style": "min-width: auto; width: 0%;"}},
    )
    ready = tables.BooleanColumn()
    state = PendingStatusColumn(verbose_name="Status")
    is_scheduled = tables.BooleanColumn(verbose_name="Scheduled")
    num_rows = RowCountColumn()
    last_synced = NaturalDayColumn(orderable=False)
    expires = NaturalDatetimeColumn(orderable=False)

    def order_num_rows(self, queryset, is_descending):
        queryset = queryset.annotate(num_rows_agg=Sum("table__num_rows")).order_by(
            ("-" if is_descending else "") + "num_rows_agg"
        )
        return (queryset, True)


class StructureTable(tables.Table):
    class Meta:
        fields = ("name", "type")
        attrs = {"class": "table-data"}

    type = tables.Column()
    name = tables.Column()


class ReferencesTable(tables.Table):
    class Meta:
        model = Integration
        attrs = {"class": "table"}
        fields = (
            "name",
            "kind",
            "created",
            "updated",
        )

    name = tables.Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
