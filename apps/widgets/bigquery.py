from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.models import Widget


def _sort(query, widget):
    """Sort widget data by label or value"""
    column = (
        query[widget.label]
        if widget.sort_by == "label"
        else query[widget.aggregations.first().column]
    )
    sort_column = [(column, widget.sort_ascending)]
    return query.sort_by(sort_column)


def get_query_from_widget(widget: Widget):

    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    values = [
        getattr(query[aggregation.column], aggregation.function)().name(
            aggregation.column
        )
        for aggregation in widget.aggregations.all()
    ]
    groups = [widget.label]
    if widget.kind in [Widget.Kind.BUBBLE, Widget.Kind.HEATMAP]:
        values += [getattr(query[widget.z], widget.z_aggregator)().name(widget.z)]
    elif widget.kind in [Widget.Kind.STACKED_BAR, Widget.Kind.STACKED_COLUMN]:
        groups += [widget.z]

    return _sort(
        query.group_by(groups).aggregate(values),
        widget,
    )
