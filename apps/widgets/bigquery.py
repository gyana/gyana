from apps.filters.bigquery import create_filter_query
from apps.widgets.models import MULTI_VALUES_CHARTS, Widget
from lib.clients import get_dataframe


def query_widget(widget: Widget):
    table = create_filter_query(widget.table.get_query(), widget.filters.all())

    if widget.aggregator == Widget.Aggregator.NONE:
        return get_dataframe(
            table.projection(
                [
                    widget.label,
                    *(
                        [widget.value]
                        if widget.kind not in MULTI_VALUES_CHARTS
                        else [value.column for value in widget.values.all()]
                    ),
                ]
            ).compile()
        )
    if widget.kind in MULTI_VALUES_CHARTS:
        return get_dataframe(
            table.group_by(widget.label)
            .aggregate(
                [
                    getattr(table[value.column], widget.aggregator)().name(value.column)
                    for value in widget.values.all()
                ]
            )
            .compile()
        )
    else:
        return get_dataframe(
            table.group_by(widget.label)
            .aggregate(
                getattr(table[widget.value], widget.aggregator)().name(widget.value)
            )
            .compile()
        )
