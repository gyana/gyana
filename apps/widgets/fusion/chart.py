import json
import uuid
from datetime import date

import numpy as np
import pandas as pd

from apps.base.core.utils import default_json_encoder
from apps.columns.bigquery import resolve_colname
from apps.columns.currency_symbols import CURRENCY_SYMBOLS_MAP
from apps.widgets.fusion.utils import DEFAULT_HEIGHT, DEFAULT_WIDTH, TO_FUSION_CHART
from apps.widgets.models import COUNT_COLUMN_NAME, NO_DIMENSION_WIDGETS, Widget

from .fusioncharts import FusionCharts


def get_unique_column_names(aggregations, groups):
    names = [
        *groups,
        *[aggregation.column for aggregation in aggregations],
    ]
    return {
        column: resolve_colname(column.column, column.function, names)
        for column in aggregations
    }


def _create_axis_names(widget):
    if widget.kind in [Widget.Kind.SCATTER, Widget.Kind.BUBBLE]:
        metrics = widget.aggregations.all()
        return {
            "xAxisName": metrics[0].column,
            "yAxisName": metrics[1].column,
        }
    if widget.kind == Widget.Kind.HEATMAP:
        return {
            "yAxisName": widget.dimension,
            "xAxisName": widget.second_dimension,
        }
    if widget.kind in NO_DIMENSION_WIDGETS:
        return {}
    if widget.category == Widget.Category.COMBO:
        primary_chart = widget.charts.filter(on_secondary=False).first()
        secondary_chart = widget.charts.filter(on_secondary=True).first()
        unique_names = get_unique_column_names(
            [primary_chart, *([secondary_chart] if secondary_chart else [])],
            [widget.dimension],
        )
        return {
            "xAxisName": widget.dimension,
            "pYAxisName": unique_names.get(primary_chart, primary_chart.column),
            **(
                {
                    "sYAxisName": unique_names.get(
                        secondary_chart, secondary_chart.column
                    )
                }
                if secondary_chart
                else {}
            ),
        }

    return {
        "xAxisName": widget.dimension,
        "yAxisName": _get_first_value_or_count(widget),
    }


def to_chart(df: pd.DataFrame, widget: Widget) -> FusionCharts:
    """Render a chart from a table."""
    pallete_colors = widget.palette_colors or widget.page.dashboard.palette_colors
    font_color = (
        widget.font_color if widget.font_color else widget.page.dashboard.font_color
    )

    data = json.loads(
        json.dumps(CHART_DATA[widget.kind](widget, df), default=default_json_encoder)
    )
    axis_names = _create_axis_names(widget)

    # All Fusioncharts attributes can be found here:
    # https://www.fusioncharts.com/dev/chart-attributes/area2d
    dataSource = {
        "chart": {
            "stack100Percent": "1" if widget.stack_100_percent else "0",
            # Themes can override each other, the values in the right-most theme
            # take precedence.
            "theme": "fusion",
            "paletteColors": ",".join(pallete_colors),
            "bgColor": widget.background_color
            or widget.page.dashboard.widget_background_color
            or "#ffffff",
            "bgAlpha": "100"
            if widget.background_color
            or widget.page.dashboard.widget_background_color != "#ffffff"
            else "0",
            "showToolTip": widget.show_tooltips
            if widget.show_tooltips is not None
            else True,
            "baseFont": widget.page.dashboard.font_family,
            "baseFontSize": widget.page.dashboard.font_size,
            "baseFontColor": font_color,
            "xAxisNameFontColor": font_color,
            "xAxisValueFontColor": font_color,
            "yAxisNameFontColor": font_color,
            "yAxisValueFontColor": font_color,
            "outCnvBaseFontColor": font_color,
            "legendItemFontColor": font_color,
            "labelFontColor": font_color,
            # Fusioncharts client-side export feature
            # TODO: If True we need to add an explicit import for
            # fusionchart.excelexport.js to our fusionchart scripts
            "exportenabled": False,
            "exportmode": "client",
            "exportFileName": widget.name if widget.name else "untitled_chart",
            **(
                {"showLabels": "0"}
                if widget.kind in [Widget.Kind.PIE, Widget.Kind.DONUT]
                else {}
            ),
            **(
                {"numberPrefix": CURRENCY_SYMBOLS_MAP[widget.currency]}
                if widget.currency
                else {}
            ),
            **(
                {
                    "lowerLimit": str(widget.lower_limit),
                    "upperLimit": str(widget.upper_limit),
                }
                if widget.kind == Widget.Kind.GAUGE
                else {}
            ),
            **axis_names,
        },
        **data,
    }

    chart_id = f"{widget.pk}-{uuid.uuid4()}"
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


def format_label(value):
    return value.strftime("%b %-d %Y") if isinstance(value, date) else str(value)


def _get_first_value_or_count(widget):
    aggregation = widget.aggregations.first()
    return aggregation.column if aggregation else COUNT_COLUMN_NAME


def to_multi_value_data(widget, df):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    values = [unique_names.get(value, value.column) for value in aggregations] or [
        COUNT_COLUMN_NAME
    ]

    return {
        "categories": [
            {
                "category": [
                    {"label": format_label(dimension)}
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
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    x, y = [unique_names.get(value, value.column) for value in aggregations][:2]
    df = df.rename(columns={x: "x", y: "y"})
    return {
        "dataset": [
            {
                "data": df[["x", "y"]].to_dict(orient="records"),
            }
        ],
    }


def to_radar(widget, df):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    df = df.melt(value_vars=[unique_names.get(col, col.column) for col in aggregations])
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
                _get_first_value_or_count(widget): "value",
            }
        ).to_dict(orient="records")
    }


def to_segment(widget, df):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [])
    df = df.melt(value_vars=[unique_names.get(col, col.column) for col in aggregations])
    return {
        "data": [
            {"label": row.variable, "value": row.value} for _, row in df.iterrows()
        ]
    }


def to_bubble(widget, df):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    x, y, z = [unique_names.get(value, value.column) for value in aggregations][:3]
    df = df.rename(columns={x: "x", y: "y", z: "z", widget.dimension: "id"})
    return {
        "categories": [
            {"category": [{"label": format_label(x)} for x in df.x.to_list()]}
        ],
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
            _get_first_value_or_count(widget): "value",
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
    if not widget.second_dimension:
        return to_multi_value_data(widget, df)
    pivoted = df.pivot(
        index=widget.dimension,
        columns=widget.second_dimension,
        values=_get_first_value_or_count(widget),
    ).reindex(df[widget.dimension].unique())

    return {
        "categories": [
            {
                "category": [
                    {"label": format_label(dimension)} for dimension in pivoted.index
                ]
            }
        ],
        "dataset": [
            {
                "seriesname": format_label(color),
                "data": [{"value": value} for value in pivoted[color].to_list()],
            }
            for color in pivoted.columns
        ],
    }


def to_combo_chart(widget, df):
    charts = widget.charts.all()
    unique_names = get_unique_column_names(charts, [widget.dimension])
    return {
        "categories": [
            {
                "category": [
                    {"label": format_label(dimension)}
                    for dimension in df[widget.dimension].to_list()
                ]
            }
        ],
        "dataset": [
            {
                "seriesname": chart.column,
                "renderAs": chart.kind,
                "parentYAxis": "S" if chart.on_secondary else "P",
                "data": [
                    {"value": value}
                    for value in df[unique_names.get(chart, chart.column)].to_list()
                ],
            }
            for chart in charts
        ],
    }


def to_gauge(widget, df):
    value = df[widget.aggregations.first().column][0]
    min_val, first_quarter, second_quarter, third_quarter, max_val = [
        int(x) for x in np.linspace(widget.lower_limit, widget.upper_limit, 5)
    ]
    return {
        "colorRange": {
            "color": [
                {
                    "minValue": str(min_val),
                    "maxValue": str(first_quarter),
                    "code": widget.first_segment_color or "#e30303",
                },
                {
                    "minValue": str(first_quarter),
                    "maxValue": str(second_quarter),
                    "code": widget.second_segment_color or "#f38e4f",
                },
                {
                    "minValue": str(second_quarter),
                    "maxValue": str(third_quarter),
                    "code": widget.third_segment_color or "#facc15",
                },
                {
                    "minValue": str(third_quarter),
                    "maxValue": str(max_val),
                    "code": widget.fourth_segment_color or "#0db145",
                },
            ]
        },
        "dials": {"dial": [{"value": str(value)}]},
    }


CHART_DATA = {
    Widget.Kind.BUBBLE: to_bubble,
    Widget.Kind.HEATMAP: to_heatmap,
    Widget.Kind.SCATTER: to_scatter,
    Widget.Kind.RADAR: to_radar,
    Widget.Kind.FUNNEL: to_segment,
    # Widget.Kind.PYRAMID: to_segment,
    Widget.Kind.PIE: to_single_value,
    Widget.Kind.DONUT: to_single_value,
    Widget.Kind.COLUMN: to_multi_value_data,
    Widget.Kind.STACKED_COLUMN: to_stack,
    Widget.Kind.BAR: to_multi_value_data,
    Widget.Kind.STACKED_BAR: to_stack,
    Widget.Kind.AREA: to_multi_value_data,
    Widget.Kind.LINE: to_multi_value_data,
    Widget.Kind.STACKED_LINE: to_stack,
    Widget.Kind.COMBO: to_combo_chart,
    Widget.Kind.GAUGE: to_gauge,
}
