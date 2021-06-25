import pandas as pd
from apps.widgets.models import Widget

from lib.fusioncharts import FusionCharts

DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "100%"


def to_chart(df: pd.DataFrame, widget: Widget) -> FusionCharts:

    """Render a chart from a table."""
    if widget.kind in [Widget.Kind.SCATTER.value]:
        data = {
            "dataset": [
                {
                    "data": df.rename(
                        columns={widget.label: "x", widget.value: "y"}
                    ).to_dict(orient="records")
                }
            ]
        }
    else:
        data = {
            "data": df.rename(
                columns={widget.label: "label", widget.value: "value"}
            ).to_dict(orient="records")
        }

    dataSource = {
        "chart": {
            "theme": "fusion",
            "xAxisName": widget.label,
            "yAxisName": widget.value,
        },
        **data,
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
