from typing import Any, Dict

from apps.base import clients
from apps.base.core.table_data import get_table
from apps.columns.bigquery import aggregate_columns, resolve_colname
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


def pre_filter(widget, control, use_previous_period=False):
    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    if (
        control := (widget.control if widget.has_control else control)
    ) and widget.date_column:
        query = slice_query(query, widget.date_column, control, use_previous_period)
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


def get_summary_row(query, widget):
    # Only naming the first group column
    group = widget.columns.first()
    aggregations = widget.aggregations.all()
    column_names = [agg.column for agg in aggregations]
    aggregations = [
        getattr(query[agg.column], agg.function)().name(
            resolve_colname(agg.column, agg.function, column_names)
        )
        for agg in aggregations
    ]
    query = query.aggregate(aggregations)
    summary = clients.bigquery().get_query_results(query.compile()).rows_dict[0]
    return {
        **{key: round(value, 2) for key, value in summary.items()},
        group.column: "Total",
    }


def table_to_output(widget: Widget, control) -> Dict[str, Any]:
    query = pre_filter(widget, control)
    summary = None
    if widget.columns.first():
        if widget.show_summary_row:
            # TODO: add sorting and limit
            summary = get_summary_row(query, widget)
        query = aggregate_columns(query, widget)

    settings = {
        col.column: {
            "name": col.name,
            "rounding": col.rounding,
            "currency": col.currency,
        }
        for col in [*widget.columns.all(), *widget.aggregations.all()]
    }

    if widget.sort_column:
        query = query.sort_by([(widget.sort_column, widget.sort_ascending)])
    return get_table(query.schema(), query, summary, settings)


def metric_to_output(widget, control, use_previous_period=False):
    query = pre_filter(widget, control, use_previous_period)

    aggregation = widget.aggregations.first()
    query = getattr(query[aggregation.column], aggregation.function)().name(
        aggregation.column
    )

    return (
        clients.bigquery()
        .get_query_results(query.compile())
        .rows_dict[0][aggregation.column]
    )
