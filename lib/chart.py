import pandas as pd
from apps.widgets.models import MULTI_VALUES_CHARTS, Widget

from lib.fusioncharts import FusionCharts

DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "100%"


def to_chart(df: pd.DataFrame, widget: Widget) -> FusionCharts:

    """Render a chart from a table."""
    if widget.kind == Widget.Kind.SCATTER.value:
        data = to_scatter(widget, df)
    elif widget.kind == Widget.Kind.RADAR.value:
        data = to_radar(widget, df)
    elif widget.kind in MULTI_VALUES_CHARTS:
        data = to_multi_value_data(widget, df)
    else:
        data = to_single_value(widget, df)

    dataSource = {
        "chart": {
            "theme": "fusion",
            "xAxisName": widget.label,
            "yAxisName": widget.values.first().column,
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


def to_multi_value_data(widget, df):
    values = widget.values.all()
    return {
        "categories": [
            {"category": [{"label": label} for label in df[widget.label].to_list()]}
        ],
        "dataset": [
            {
                **({"seriesname": value.column} if len(values) > 1 else dict()),
                "data": [{"value": value} for value in df[value.column].to_list()],
            }
            for value in values
        ],
    }


def to_scatter(widget, df):
    values = widget.values.all()
    df = df.rename(columns={widget.label: "x"})
    return {
        "categories": [{"category": [{"label": label} for label in df.x.to_list()]}],
        "dataset": [
            {
                **({"seriesname": value.column} if len(values) > 1 else dict()),
                "data": df.rename(columns={value.column: "y"})[["x", "y"]].to_dict(
                    orient="records"
                ),
            }
            for value in values
        ],
    }


def to_radar(widget, df):
    return {
        "categories": [
            {"category": [{"label": label} for label in df[widget.label].to_list()]}
        ],
        "dataset": [
            {
                "data": [
                    {"value": value}
                    for value in df[widget.values.first().column].to_list()
                ],
            }
        ],
    }


def to_single_value(widget, df):
    return {
        "data": df.rename(
            columns={widget.label: "label", widget.values.first().column: "value"}
        ).to_dict(orient="records")
    }
