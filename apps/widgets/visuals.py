from typing import Any, Dict

from apps.base import clients
from apps.base.table_data import get_table
from apps.controls.bigquery import slice_query
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.fusion.timeseries import TIMESERIES_DATA, to_timeseries

from .bigquery import get_query_from_widget
from .fusion.chart import to_chart
from .models import Widget

CHART_MAX_ROWS = 1000


class MaxRowsExceeded(Exception):
    pass


def pre_filter(widget, control):
    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    if control and widget.date_column:
        query = slice_query(query, widget.date_column, control)
    return query


def chart_to_output(widget: Widget, control) -> Dict[str, Any]:
    query = pre_filter(widget, control)
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


def get_summary_row(query, aggregations, groups):
    query = query.aggregate(aggregations)
    summary = clients.bigquery().get_query_results(query.compile()).rows_dict[0]
    return {**summary, **{group.column: "Total:" for group in groups}}


def table_to_output(widget: Widget, control) -> Dict[str, Any]:
    query = pre_filter(widget, control)

    groups = widget.columns.all()
    aggregations = [
        getattr(query[agg.column], agg.function)().name(agg.column)
        for agg in widget.aggregations.all()
    ]
    if widget.show_summary_row:
        summary = get_summary_row(query, aggregations, groups)

    if groups:
        query = query.group_by([col.column for col in groups])
    if aggregations:
        query = query.aggregate(aggregations)

    return get_table(
        query.schema(), query, summary if widget.show_summary_row else None
    )


def metric_to_output(widget, control):
    query = pre_filter(widget, control)

    aggregation = widget.aggregations.first()
    query = getattr(query[aggregation.column], aggregation.function)().name(
        aggregation.column
    )

    return (
        clients.bigquery()
        .get_query_results(query.compile())
        .rows_dict[0][aggregation.column]
    )
