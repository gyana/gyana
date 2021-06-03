from apps.filters.bigquery import create_filter_query
from apps.filters.models import Filter
from apps.widgets.models import Widget
from lib.clients import ibis_client


def query_widget(widget: Widget):

    conn = ibis_client()

    table = create_filter_query(widget.table.get_query(), widget.filters.all())

    if widget.aggregator == Widget.Aggregator.NONE:
        return conn.execute(table.projection([widget.label, widget.value]))
    else:
        return conn.execute(
            table.group_by(widget.label).aggregate(
                getattr(table[widget.value], widget.aggregator)().name(widget.value)
            )
        )
