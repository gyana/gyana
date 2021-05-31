import json
from typing import Any

import pandas as pd
from django.forms.widgets import Widget

from lib.fusioncharts import FusionCharts

DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "400"


def to_chart(df: pd.DataFrame, widget: Widget) -> FusionCharts:

    """Render a chart from a table."""

    df = df.rename(columns={widget.label: "label", widget.value: "value"})

    dataSource = {
        "chart": {
            "theme": "fusion",
            "xAxisName": widget.label,
            "yAxisName": widget.value,
        },
        "data": df.to_dict(orient="records"),
    }

    return FusionCharts(
        widget.kind,
        f"chart-{widget.pk}",
        DEFAULT_WIDTH,
        DEFAULT_HEIGHT,
        f"chart-{widget.pk}-container",
        "json",
        dataSource,
    )
