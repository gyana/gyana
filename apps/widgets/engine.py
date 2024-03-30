import ibis
from ibis.expr import datatypes as idt

from apps.columns.engine import PART_MAP, aggregate_columns
from apps.widgets.models import NO_DIMENSION_WIDGETS, Widget


def _sort(query, widget):
    """Sort widget data by label or value"""
    if widget.sort_column and widget.sort_column in query:
        column = query[widget.sort_column]
        if widget.kind in [Widget.Kind.STACKED_BAR, Widget.Kind.STACKED_COLUMN]:
            column = (
                column.sum()
                .over(ibis.window(group_by=widget.dimension))
                .name("__widget_sort_column_stacked__")
            )
    elif widget.dimension and widget.dimension in query:
        column = query[widget.dimension]
    else:
        return query
    if not widget.sort_ascending:
        column = column.desc()
    sort_column = [column]
    return query.order_by(sort_column)


def get_query_from_widget(widget: Widget, query):
    aggregations = widget.aggregations.all()

    if widget.category == Widget.Category.COMBO:
        aggregations = widget.charts.all()
    else:
        aggregations = widget.aggregations.all()

    if widget.kind in NO_DIMENSION_WIDGETS:
        groups = []
    elif (
        (group_column := query[widget.dimension]) is not None
        and isinstance(group_column.type(), (idt.Date, idt.Timestamp))
        and widget.part
    ):
        groups = [PART_MAP[widget.part](group_column).name(widget.dimension)]
    else:
        groups = [group_column]
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
        groups += [query[widget.second_dimension]]

    query = aggregate_columns(query, aggregations, groups)
    if widget.kind in NO_DIMENSION_WIDGETS:
        return query

    return _sort(
        query,
        widget,
    )
