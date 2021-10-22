from typing import Any, Dict

from apps.base import clients
from apps.base.table_data import get_table
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table

from .bigquery import get_query_from_widget
from .chart import to_chart
from .models import Widget

CHART_MAX_ROWS = 1000


class MaxRowsExceeded(Exception):
    pass


def chart_to_output(widget: Widget) -> Dict[str, Any]:
    result = clients.bigquery().get_query_results(
        get_query_from_widget(widget).compile(), max_results=CHART_MAX_ROWS
    )
    if result.total_rows > CHART_MAX_ROWS:
        raise MaxRowsExceeded
    df = result.rows_df
    chart, chart_id = to_chart(df, widget)
    return {"chart": chart.render()}, chart_id


def table_to_output(widget: Widget) -> Dict[str, Any]:
    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    return get_table(query.schema(), query)
