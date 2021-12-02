from typing import Any, Dict

from apps.base import clients
from apps.base.table_data import get_table
from apps.dateslicers.bigquery import slice_query
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.fusion.timeseries import TIMESERIES_DATA, to_timeseries

from .bigquery import get_query_from_widget
from .fusion.chart import to_chart
from .models import Widget

CHART_MAX_ROWS = 1000


class MaxRowsExceeded(Exception):
    pass


def pre_filter(widget, date_slicer):
    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    if date_slicer and widget.dateslice_column:
        query = slice_query(query, widget.dateslice_column, date_slicer)
    return query


def chart_to_output(widget: Widget, date_slicer) -> Dict[str, Any]:
    query = pre_filter(widget, date_slicer)
    query = get_query_from_widget(widget, query)
    result = clients.bigquery().get_query_results(
        query.compile(), max_results=CHART_MAX_ROWS
    )
    if (result.total_rows or 0) > CHART_MAX_ROWS:
        raise MaxRowsExceeded
    df = result.rows_df

    if widget.kind in TIMESERIES_DATA:
        chart, chart_id = to_timeseries(widget, df, query)
    else:
        chart, chart_id = to_chart(df, widget)

    return {"chart": chart.render()}, chart_id


def table_to_output(widget: Widget, date_slicer) -> Dict[str, Any]:
    query = pre_filter(widget, date_slicer)

    return get_table(query.schema(), query)


def metric_to_output(widget, date_slicer):
    query = pre_filter(widget, date_slicer)

    aggregation = widget.aggregations.first()
    query = getattr(query[aggregation.column], aggregation.function)().name(
        aggregation.column
    )

    return (
        clients.bigquery()
        .get_query_results(query.compile())
        .rows_dict[0][aggregation.column]
    )
