import ibis
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.models import COUNT_COLUMN_NAME, NO_DIMENSION_WIDGETS, Widget


def _sort(query, widget):
    """Sort widget data by label or value"""
    if widget.sort_by == "dimension" and widget.dimension:
        column = query[widget.dimension]
    elif first_aggregation := widget.aggregations.first():
        column = query[first_aggregation.column]
        if widget.kind in [Widget.Kind.STACKED_BAR, Widget.Kind.STACKED_COLUMN]:
            column = (
                column.sum()
                .over(ibis.window(group_by=widget.dimension))
                .name("__widget_sort_column_stacked__")
            )
    else:
        return query
    sort_column = [(column, widget.sort_ascending)]
    return query.sort_by(sort_column)


def get_unique_column_names(aggregations, groups):
    column_names = [*groups, *[aggregation.column for aggregation in aggregations]]
    return {
        aggregation: f"{aggregation.column}_{aggregation.function}"
        for aggregation in aggregations
        if column_names.count(aggregation.column) > 1
    }


def get_query_from_widget(widget: Widget):

    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    aggregations = widget.aggregations.all()

    groups = [widget.dimension] if widget.kind not in NO_DIMENSION_WIDGETS else []
    if (
        widget.kind
        in [
            Widget.Kind.HEATMAP,
            Widget.Kind.STACKED_BAR,
            Widget.Kind.STACKED_COLUMN,
            Widget.Kind.STACKED_LINE,
            Widget.Kind.TIMESERIES_STACKED_LINE,
            Widget.Kind.TIMESERIES_STACKED_COLUMN,
        ]
        and widget.second_dimension
    ):
        groups += [widget.second_dimension]

    unique_names = get_unique_column_names(aggregations, groups)

    values = (
        [
            getattr(query[aggregation.column], aggregation.function)().name(
                unique_names.get(aggregation, aggregation.column)
            )
            for aggregation in aggregations
        ]
        if aggregations
        else [query.count().name(COUNT_COLUMN_NAME)]
    )

    query = query.group_by(groups).aggregate(values)
    if widget.kind in NO_DIMENSION_WIDGETS:
        return query

    return _sort(
        query,
        widget,
    )
