from typing import Any, Dict

from apps.base.clients import get_engine
from apps.base.core.table_data import get_table
from apps.columns.engine import aggregate_columns, get_groups
from apps.controls.engine import slice_query
from apps.filters.engine import get_query_from_filters

from .engine import get_query_from_widget
from .models import Widget
from .plotly.chart import to_chart

CHART_MAX_ROWS = 1000


class MaxRowsExceeded(Exception):
    pass


def pre_filter(widget, control, use_previous_period=False):
    query = get_engine().get_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    if (
        control := (widget.control if widget.has_control else control)
    ) and widget.date_column:
        query = slice_query(query, widget.date_column, control, use_previous_period)
    return query


def chart_to_output(widget: Widget, control) -> Dict[str, Any]:
    query = pre_filter(widget, control)
    query = get_query_from_widget(widget, query)

    # limit to 1001 rows to check if chart exceeds max rows
    df = query.limit(CHART_MAX_ROWS + 1).execute()
    if len(df) > CHART_MAX_ROWS:
        raise MaxRowsExceeded

    chart, chart_id = to_chart(df, widget)

    return {"chart": chart}, chart_id


def get_summary_row(query, widget):
    # Only naming the first group column
    group = widget.columns.first()

    query = aggregate_columns(query, widget.aggregations.all(), None)
    summary = query.execute().iloc[0].to_dict()

    return {**summary, group.column: "Total"}


def table_to_output(widget: Widget, control, url=None) -> Dict[str, Any]:
    query = pre_filter(widget, control)
    summary = None
    if (group := widget.columns.first()) or widget.aggregations.first():
        # Only show summary row when a group has been selected
        if widget.show_summary_row and group:
            # TODO: add sorting and limit
            summary = get_summary_row(query, widget)
        groups = get_groups(query, widget)
        if widget.aggregations.exists():
            query = aggregate_columns(query, widget.aggregations.all(), groups)
        else:
            query = query[groups]

    settings = {
        col.column: {
            "name": col.name,
            "rounding": col.rounding,
            "currency": col.currency,
            "is_percentage": col.is_percentage,
            "conditional_formatting": col.conditional_formatting,
            "positive_threshold": col.positive_threshold,
            "negative_threshold": col.negative_threshold,
        }
        for col in [*widget.columns.all(), *widget.aggregations.all()]
    }
    settings["hide_data_type"] = widget.table_hide_data_type

    if widget.sort_column:
        query = query.order_by([(widget.sort_column, widget.sort_ascending)])

    return get_table(query.schema(), query, summary, settings, url=url)


def metric_to_output(widget, control, use_previous_period=False):
    query = pre_filter(widget, control, use_previous_period)

    aggregation = widget.aggregations.first()
    query = getattr(query[aggregation.column], aggregation.function)().name(
        aggregation.column
    )

    return query.execute()
