import random
import string

import numpy as np
import pandas as pd
from apps.widgets.models import NO_DIMENSION_WIDGETS, Widget

from .fusioncharts import FusionCharts


def short_hash():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for n in range(6)
    )


DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "100%"

TO_FUSION_CHART = {Widget.Kind.STACKED_LINE: "msline"}


def _create_axis_names(widget):
    if widget.kind in [Widget.Kind.SCATTER, Widget.Kind.BUBBLE]:
        metrics = widget.aggregations.all()
        return {
            "xAxisName": metrics[0].column,
            "yAxisName": metrics[1].column,
        }
    if widget.kind == Widget.Kind.HEATMAP:
        return {
            "xAxisName": widget.dimension,
            "yAxisName": widget.second_dimension,
        }
    if widget.kind in NO_DIMENSION_WIDGETS:
        {}
    return {
        "xAxisName": widget.dimension,
        "yAxisName": widget.aggregations.first().column,
    }


def to_chart(df: pd.DataFrame, widget: Widget) -> FusionCharts:
    """Render a chart from a table."""

    data = CHART_DATA[widget.kind](widget, df)
    axis_names = _create_axis_names(widget)
    dataSource = {
        "chart": {
            "stack100Percent": "1" if widget.stack_100_percent else "0",
            "theme": "fusion",
            **axis_names,
        },
        **data,
    }

    chart_id = f"{widget.pk}-{short_hash()}"
    return (
        FusionCharts(
            TO_FUSION_CHART.get(widget.kind) or widget.kind,
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
    values = [value.column for value in widget.aggregations.all()]
    return {
        "categories": [
            {
                "category": [
                    {"label": str(dimension)}
                    for dimension in df[widget.dimension].to_list()
                ]
            }
        ],
        "dataset": [
            {
                **({"seriesname": value} if len(values) > 1 else dict()),
                "data": [{"value": value} for value in df[value].to_list()],
            }
            for value in values
        ],
    }


def to_scatter(widget, df):
    x, y = [value.column for value in widget.aggregations.all()]
    df = df.rename(columns={x: "x", y: "y", widget.dimension: "id"})
    return {
        "categories": [{"category": [{"label": str(x)} for x in df.x.to_list()]}],
        "dataset": [
            {
                "data": df[["x", "y", "id"]].to_dict(orient="records"),
            }
        ],
    }


def to_radar(widget, df):
    df = df.melt(value_vars=[col.column for col in widget.aggregations.all()])
    return {
        "categories": [
            {"category": [{"label": label} for label in df.variable.to_list()]}
        ],
        "dataset": [
            {
                "data": [{"value": value} for value in df.value.to_list()],
            }
        ],
    }


def to_single_value(widget, df):
    return {
        "data": df.rename(
            columns={
                widget.dimension: "label",
                widget.aggregations.first().column: "value",
            }
        ).to_dict(orient="records")
    }


def to_segment(widget, df):
    df = df.melt(
        value_vars=[
            col.column
            for col in widget.aggregations.order_by(
                "created" if widget.kind == Widget.Kind.FUNNEL else "-created"
            ).all()
        ]
    )
    return {
        "data": [
            {"label": row.variable, "value": row.value} for _, row in df.iterrows()
        ]
    }


def to_bubble(widget, df):
    x, y, z = [value.column for value in widget.aggregations.all()]
    df = df.rename(columns={x: "x", y: "y", z: "z", widget.dimension: "id"})
    return {
        "categories": [{"category": [{"label": str(x)} for x in df.x.to_list()]}],
        "dataset": [
            {
                "data": df[["x", "y", "z", "id"]].to_dict(orient="records"),
            }
        ],
    }


COLOR_CODES = ["0155E8", "2BA8E8", "21C451", "FFD315", "E8990C", "C24314", "FF0000"]


def to_heatmap(widget, df):
    df = df.rename(
        columns={
            widget.dimension: "rowid",
            widget.second_dimension: "columnid",
            widget.aggregations.first().column: "value",
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
        index=widget.dimension,
        columns=widget.second_dimension,
        values=widget.aggregations.first().column,
    )

    if widget.sort_by == "value":
        pivoted = pivoted.reindex(df[widget.dimension].unique())
    return {
        "categories": [
            {"category": [{"label": str(dimension)} for dimension in pivoted.index]}
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
    Widget.Kind.FUNNEL: to_segment,
    Widget.Kind.PYRAMID: to_segment,
    Widget.Kind.PIE: to_single_value,
    Widget.Kind.DONUT: to_single_value,
    Widget.Kind.COLUMN: to_multi_value_data,
    Widget.Kind.STACKED_COLUMN: to_stack,
    Widget.Kind.BAR: to_multi_value_data,
    Widget.Kind.STACKED_BAR: to_stack,
    Widget.Kind.AREA: to_multi_value_data,
    Widget.Kind.LINE: to_multi_value_data,
    Widget.Kind.STACKED_LINE: to_stack,
}
