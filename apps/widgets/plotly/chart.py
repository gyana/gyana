import uuid
from functools import partial

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from apps.widgets.fusion.chart import _get_first_value_or_count, get_unique_column_names
from apps.widgets.models import COUNT_COLUMN_NAME, Widget


def get_metrics(widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    return [unique_names.get(value, value.column) for value in aggregations] or [
        COUNT_COLUMN_NAME
    ]


def to_line(df, widget):
    values = get_metrics(widget)

    return go.Figure(
        data=[
            go.Scatter(
                x=df[widget.dimension],
                y=df[value],
                mode="lines+markers",
                line_shape="spline",
                name=value,
            )
            for value in values
        ],
        layout=go.Layout(
            title=widget.name,
        ),
    )


def to_line_stack(df, widget):
    if not widget.second_dimension:
        return to_line(df, widget)
    return px.line(
        df,
        x=widget.dimension,
        y=_get_first_value_or_count(widget),
        markers=True,
        line_shape="spline",
        color=widget.second_dimension,
        title=widget.name,
    )


def to_column(df, widget, orientation="v"):
    values = get_metrics(widget)

    fig = go.Figure(
        data=[
            go.Bar(
                name=value, x=df[value], y=df[widget.dimension], orientation=orientation
            )
            for value in values
        ]
    )
    # Change the bar mode
    fig.update_layout(barmode="group")
    return fig


def to_column_stack(df, widget, orientation="v"):
    if not widget.second_dimension:
        return to_column(df, widget, orientation)

    return px.bar(
        df,
        x=widget.dimension,
        y=_get_first_value_or_count(widget),
        color=widget.second_dimension,
        title=widget.name,
    )


def to_pie(df, widget):
    return px.pie(
        df,
        names=widget.dimension,
        values=_get_first_value_or_count(widget),
        title=widget.name,
        hole=0.3 if Widget.Kind.DONUT else None,
    )


def to_scatter(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    x, y = [unique_names.get(value, value.column) for value in aggregations][:2]

    return px.scatter(df, x=x, y=y, title=widget.name)


def to_bubble(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    x, y, z = [unique_names.get(value, value.column) for value in aggregations][:3]
    return px.scatter(df, x=x, y=y, size=z)


def pivot_df(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    return df.melt(
        value_vars=[unique_names.get(col, col.column) for col in aggregations]
    )


def to_radar(df, widget):
    df = pivot_df(df, widget)
    return px.line_polar(df, r="variable", theta="value", line_close=True)


def to_funnel(df, widget):
    df = pivot_df(df, widget)
    return px.funnel_area(df, x="variable", y="value")


def to_area(df, widget):
    values = get_metrics(widget)

    return go.Figure(
        data=[
            go.Area(
                name=value,
                x=df[widget.dimension],
                y=df[value],
                fill="tozeroy" if i == 0 else "tonexty",
            )
            for i, value in enumerate(values)
        ],
        title=widget.name,
    )


def to_heatmap(df, widget):
    df = df.pivot(
        index=widget.dimension,
        columns=widget.second_dimension,
        values=_get_first_value_or_count(widget),
    )
    return px.imshow(df, title=widget.name)


def to_gauge(df, widget):
    value = df[widget.aggregations.first().column][0]
    min_val, first_quarter, second_quarter, third_quarter, max_val = [
        int(x) for x in np.linspace(widget.lower_limit, widget.upper_limit, 5)
    ]
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title=widget.name,
            gauge={
                "axis": [min_val, max_val],
                "steps": [
                    {
                        "range": [min_val, first_quarter],
                        "color": widget.first_segment_color or "#e30303",
                    },
                    {
                        "range": [first_quarter, second_quarter],
                        "color": widget.second_segment_color or "#f38e4f",
                    },
                    {
                        "range": [second_quarter, third_quarter],
                        "color": widget.third_segment_color or "#facc15",
                    },
                    {
                        "range": [third_quarter, max_val],
                        "color": widget.fourth_segment_color or "#0db145",
                    },
                ],
            },
        )
    )


def to_chart(df, widget):
    fig = CHART_FIG[widget.kind](df, widget)
    chart = plot(fig, output_type="div", include_plotlyjs=False)
    chart_id = f"{widget.pk}-{uuid.uuid4()}"

    return chart, chart_id


CHART_FIG = {
    Widget.Kind.BUBBLE: to_bubble,
    Widget.Kind.HEATMAP: to_heatmap,
    Widget.Kind.SCATTER: to_scatter,
    Widget.Kind.RADAR: to_radar,
    Widget.Kind.FUNNEL: to_funnel,
    # Widget.Kind.PYRAMID: to_segment,
    Widget.Kind.PIE: to_pie,
    Widget.Kind.DONUT: to_pie,
    Widget.Kind.COLUMN: to_column,
    Widget.Kind.STACKED_COLUMN: to_column_stack,
    Widget.Kind.BAR: partial(to_column, orientation="h"),
    Widget.Kind.STACKED_BAR: partial(to_column_stack, orientation="h"),
    Widget.Kind.AREA: to_area,
    Widget.Kind.LINE: to_line,
    Widget.Kind.STACKED_LINE: to_line_stack,
    # Widget.Kind.COMBO: to_combo_chart,
    Widget.Kind.GAUGE: to_gauge,
}
