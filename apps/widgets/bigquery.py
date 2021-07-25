from apps.filters.bigquery import create_filter_query
from apps.widgets.models import MULTI_VALUES_CHARTS, Widget
from lib.clients import get_dataframe
from apps.tables.bigquery import get_query_from_table


def query_widget(widget: Widget):
    table = create_filter_query(
        get_query_from_table(widget.table), widget.filters.all()
    )
    values = [value.column for value in widget.values.all()]
    if widget.kind in [Widget.Kind.BUBBLE, Widget.Kind.HEATMAP]:
        values += [widget.z]
    if widget.aggregator == Widget.Aggregator.NONE:
        return get_dataframe(table.projection([widget.label, *values]).compile())
    else:
        return get_dataframe(
            table.group_by(widget.label)
            .aggregate(
                [
                    getattr(table[value], widget.aggregator)().name(value)
                    for value in values
                ]
            )
            .compile()
        )
