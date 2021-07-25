from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.models import Widget


def get_query_from_widget(widget: Widget):

    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    values = [value.column for value in widget.values.all()]
    if widget.kind in [Widget.Kind.BUBBLE, Widget.Kind.HEATMAP]:
        values += [widget.z]

    if widget.aggregator == Widget.Aggregator.NONE:
        return query.projection([widget.label, *values])

    return query.group_by(widget.label).aggregate(
        [getattr(query[value], widget.aggregator)().name(value) for value in values]
    )
