import json
from typing import Any, Dict

from apps.filters.bigquery import get_query_from_filters
from apps.integrations.bigquery import DEFAULT_LIMIT
from apps.tables.bigquery import get_query_from_table
from apps.utils.clients import get_dataframe

from .bigquery import get_query_from_widget
from .chart import to_chart
from .models import Widget


def chart_to_output(widget: Widget) -> Dict[str, Any]:
    df = get_dataframe(get_query_from_widget(widget).compile())
    chart, chart_id = to_chart(df, widget)
    return {"chart": chart.render()}, chart_id


def table_to_output(widget: Widget) -> Dict[str, Any]:
    table = get_query_from_filters(
        get_query_from_table(widget.table), widget.filters.all()
    )

    df = get_dataframe(table.limit(DEFAULT_LIMIT).compile())

    return {
        "columns": json.dumps([{"field": col} for col in df.columns]),
        "rows": df.to_json(orient="records"),
    }
