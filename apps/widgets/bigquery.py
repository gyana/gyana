import ibis
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.models import NO_DIMENSION_WIDGETS, Widget


def _sort(query, widget):
    """Sort widget data by label or value"""
    if widget.sort_by == "dimension" and widget.dimension:
        column = query[widget.dimension]
    else:
        column = query[widget.aggregations.first().column]
        if widget.kind in [Widget.Kind.STACKED_BAR, Widget.Kind.STACKED_COLUMN]:
            column = (
                column.sum()
                .over(ibis.window(group_by=widget.dimension))
                .name("__widget_sort_column_stacked__")
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
    groups = [widget.dimension] if widget.kind not in NO_DIMENSION_WIDGETS else []
    if (
        widget.kind
        in [
            Widget.Kind.HEATMAP,
            Widget.Kind.STACKED_BAR,
            Widget.Kind.STACKED_COLUMN,
            Widget.Kind.STACKED_LINE,
        ]
        and widget.second_dimension
    ):
        groups += [widget.second_dimension]

    return _sort(
        query.group_by(groups).aggregate(values),
        widget,
    )
