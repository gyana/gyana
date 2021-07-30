from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.models import Widget


def _sort(query, widget):
    """Sort widget data by label or value"""
    column = query[widget.label] if widget.sort_by == "label" else query[widget.value]
    sort_column = [(column, widget.sort_ascending)]
    return query.sort_by(sort_column)


def get_query_from_widget(widget: Widget):

    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    values = [widget.value]
    values += [value.column for value in widget.values.all()]

    if widget.kind in [Widget.Kind.BUBBLE, Widget.Kind.HEATMAP]:
        values += [widget.z]

    groups = [widget.label]

    if widget.kind in [Widget.Kind.STACKED_BAR, Widget.Kind.STACKED_COLUMN]:
        groups += [widget.z]

    if widget.aggregator == Widget.Aggregator.NONE:
        return _sort(query.projection([*groups, *values]), widget)

    return _sort(
        query.group_by(groups).aggregate(
            [getattr(query[value], widget.aggregator)().name(value) for value in values]
        ),
        widget,
    )
