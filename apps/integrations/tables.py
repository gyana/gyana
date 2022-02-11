import django_tables2 as tables
from django.db.models.aggregates import Sum
from django.template import Context
from django.template.loader import get_template
from django.utils.html import format_html

from apps.base.tables import FaBooleanColumn, NaturalDatetimeColumn, NaturalDayColumn
from apps.tables.models import Table

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
            **kwargs,
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
    ready = FaBooleanColumn()
    state = PendingStatusColumn(verbose_name="Status")
    is_scheduled = FaBooleanColumn(verbose_name="Scheduled")
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
        fields = ("name", "used_table", "kind", "created", "updated")
        attrs = {"class": "table"}

    name = tables.Column(empty_values=())
    kind = tables.Column(accessor="parent_kind")
    used_table = tables.Column(empty_values=())
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()

    def render_name(self, record):
        if record.parent_kind == "Workflow":
            return format_html(
                f"<a target='_top' href={record.workflow.get_absolute_url()}>{record.workflow.name}</a>"
            )
        return format_html(
            f"<a target='_top' href={record.page.dashboard.get_absolute_url()}>{record.page.dashboard.name}</a>"
        )

    def render_used_table(self, record):
        if record.parent_kind == "Workflow":
            table = record.input_table
        else:
            table = record.table
        table_name = (
            table.bq_table
            if table.integration.kind == Integration.Kind.CONNECTOR
            else table.integration.name
        )
        return format_html(
            f"<a target='_top' href='{table.integration.get_absolute_url()}?table_id={table.id}'>{table_name}</a>"
        )

    def render_updated(self, record):
        if record.parent_kind == "Workflow":
            return record.workflow.updated
        return record.page.dashboard.updated

    def render_created(self, record):
        if record.parent_kind == "Workflow":
            return record.workflow.created
        return record.page.dashboard.created
