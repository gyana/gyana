from typing import Any, Dict

from apps.base import clients
from apps.base.table_data import get_table
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.widgets.fusion.timeseries import CHART_DATA, to_timeseries

from .bigquery import get_query_from_widget
from .fusion.chart import to_chart
from .models import Widget

CHART_MAX_ROWS = 1000


class MaxRowsExceeded(Exception):
    pass


def chart_to_output(widget: Widget) -> Dict[str, Any]:
    query = get_query_from_widget(widget)
    result = clients.bigquery().get_query_results(
        query.compile(), max_results=CHART_MAX_ROWS
    )
    if (result.total_rows or 0) > CHART_MAX_ROWS:
        raise MaxRowsExceeded
    df = result.rows_df

    if (
        query.schema()[widget.dimension].name in ["Timestamp", "Date", "Time"]
        and widget.kind in CHART_DATA
    ):
        chart, chart_id = to_timeseries(widget, df, query)
    else:
        chart, chart_id = to_chart(df, widget)

    return {"chart": chart.render()}, chart_id


def table_to_output(widget: Widget) -> Dict[str, Any]:
    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    return get_table(query.schema(), query)
