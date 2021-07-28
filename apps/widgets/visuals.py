import json
from typing import Any, Dict

from apps.filters.bigquery import get_query_from_filters
from apps.integrations.bigquery import DEFAULT_LIMIT
from apps.tables.bigquery import get_query_from_table
from apps.utils.clients import get_dataframe
from apps.utils.table_data import get_table

from .bigquery import get_query_from_widget
from .chart import to_chart
from .models import Widget


def chart_to_output(widget: Widget) -> Dict[str, Any]:
    df = get_dataframe(get_query_from_widget(widget).compile())
    chart, chart_id = to_chart(df, widget)
    return {"chart": chart.render()}, chart_id


def table_to_output(widget: Widget) -> Dict[str, Any]:
    query = get_query_from_table(widget.table)
    query = get_query_from_filters(query, widget.filters.all())

    return get_table(query.schema(), query)
