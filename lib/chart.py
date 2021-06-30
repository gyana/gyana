import numpy as np
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
    elif widget.kind == Widget.Kind.BUBBLE.value:
        data = to_bubble(widget, df)
    elif widget.kind == Widget.Kind.HEATMAP.value:
        data = to_heatmap(widget, df)
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


def to_bubble(widget, df):
    return {
        "dataset": [
            {
                "data": df.rename(
                    columns={
                        widget.label: "x",
                        widget.values.first().column: "y",
                        widget.z: "z",
                    }
                ).to_dict(orient="records")
            }
        ],
    }


COLOR_CODES = ["0155E8", "2BA8E8", "21C451", "FFD315", "E8990C", "C24314", "FF0000"]


def to_heatmap(widget, df):
    df = df.rename(
        columns={
            widget.label: "rowid",
            widget.values.first().column: "columnid",
            widget.z: "value",
        }
    ).sort_values(["rowid", "columnid"])

    df[["rowid", "columnid"]] = df[["rowid", "columnid"]].astype(str)
    min_value, max_value = df.value.min(), df.value.max()
    min_values = np.linspace(min_value, max_value, len(COLOR_CODES) + 1)
    return {
        "dataset": [{"data": df.to_dict(orient="records")}],
        "colorrange": {
            "gradient": "0",
            "minvalue": str(min_value),
            "code": "E24B1A",
            "color": [
                {
                    "code": code,
                    "minvalue": str(min_values[i]),
                    "maxvalue": str(min_values[i + 1]),
                }
                for i, code in enumerate(COLOR_CODES)
            ],
        },
    }
