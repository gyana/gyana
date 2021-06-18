from apps.filters.bigquery import create_filter_query
from apps.widgets.models import Widget
from lib.clients import get_dataframe


def query_widget(widget: Widget):
    table = create_filter_query(widget.table.get_query(), widget.filters.all())

    if widget.aggregator == Widget.Aggregator.NONE:
        return get_dataframe(table.projection([widget.label, widget.value]).compile())
    else:
        return get_dataframe(
            table.group_by(widget.label)
            .aggregate(
                getattr(table[widget.value], widget.aggregator)().name(widget.value)
            )
            .compile()
        )
