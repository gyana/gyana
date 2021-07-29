import random
import string

import numpy as np
import pandas as pd
from apps.widgets.models import MULTI_VALUES_CHARTS, Widget

from .fusioncharts import FusionCharts


def short_hash():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for n in range(6)
    )


DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "100%"


def to_chart(df: pd.DataFrame, widget: Widget) -> FusionCharts:
    """Render a chart from a table."""

    data = CHART_DATA[widget.kind](widget, df)

    dataSource = {
        "chart": {
            "theme": "fusion",
            "xAxisName": widget.label,
            "yAxisName": widget.values.first().column,
        },
        **data,
    }

    chart_id = f"{widget.pk}-{short_hash()}"
    return (
        FusionCharts(
            widget.kind,
            f"chart-{chart_id}",
            DEFAULT_WIDTH,
            DEFAULT_HEIGHT,
            f"chart-{chart_id}-container",
            "json",
            dataSource,
        ),
        chart_id,
    )


def to_multi_value_data(widget, df):
    values = widget.values.all()
    return {
        "categories": [
            {
                "category": [
                    {"label": str(label)} for label in df[widget.label].to_list()
                ]
            }
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


def to_stack(widget, df):
    pivoted = df.pivot(
        index=widget.label, columns=widget.z, values=widget.values.first().column
    )
    return {
        "categories": [
            {"category": [{"label": str(label)} for label in pivoted.index]}
        ],
        "dataset": [
            {
                "seriesname": str(color),
                "data": [{"value": value} for value in pivoted[color].to_list()],
            }
            for color in pivoted.columns
        ],
    }


CHART_DATA = {
    Widget.Kind.BUBBLE: to_bubble,
    Widget.Kind.HEATMAP: to_heatmap,
    Widget.Kind.SCATTER: to_scatter,
    Widget.Kind.RADAR: to_radar,
    Widget.Kind.FUNNEL: to_single_value,
    Widget.Kind.PYRAMID: to_single_value,
    Widget.Kind.PIE: to_single_value,
    Widget.Kind.DONUT: to_single_value,
    Widget.Kind.COLUMN: to_multi_value_data,
    Widget.Kind.STACKED_COLUMN: to_stack,
    Widget.Kind.BAR: to_multi_value_data,
    Widget.Kind.STACKED_BAR: to_stack,
    Widget.Kind.AREA: to_multi_value_data,
    Widget.Kind.LINE: to_multi_value_data,
}
