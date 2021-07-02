import json
from typing import Any, Dict

from apps.filters.bigquery import create_filter_query
from apps.integrations.bigquery import DEFAULT_LIMIT
from lib.chart import to_chart
from lib.clients import get_dataframe

from .bigquery import query_widget
from .models import Widget


def chart_to_output(widget: Widget) -> Dict[str, Any]:
    df = query_widget(widget)
    chart, chart_id = to_chart(df, widget)
    return {"chart": chart.render()}, chart_id


def table_to_output(widget: Widget) -> Dict[str, Any]:
    table = create_filter_query(widget.table.get_query(), widget.filters.all())

    df = get_dataframe(table.limit(DEFAULT_LIMIT).compile())

    return {
        "columns": json.dumps([{"field": col} for col in df.columns]),
        "rows": df.to_json(orient="records"),
    }
