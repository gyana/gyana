import uuid
from functools import partial

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from apps.columns.bigquery import resolve_colname
from apps.widgets.models import COUNT_COLUMN_NAME, CombinationChart, Widget


def _get_first_value_or_count(widget):
    aggregation = widget.aggregations.first()
    return aggregation.column if aggregation else COUNT_COLUMN_NAME


def get_unique_column_names(aggregations, groups):
    names = [
        *groups,
        *[aggregation.column for aggregation in aggregations],
    ]
    return {
        column: resolve_colname(column.column, column.function, names)
        for column in aggregations
    }


def get_pallete_colors(widget):
    return widget.palette_colors or widget.page.dashboard.palette_colors


def get_metrics(widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    return [unique_names.get(value, value.column) for value in aggregations] or [
        COUNT_COLUMN_NAME
    ]


def to_line(df, widget):
    values = get_metrics(widget)
    pallete_colors = get_pallete_colors(widget)
    return go.Figure(
        data=[
            go.Scatter(
                x=df[widget.dimension],
                y=df[value],
                mode="lines+markers",
                line_shape="spline",
                name=value,
                marker={
                    "color": pallete_colors[i if i < len(values) else i % len(values)]
                },
                line={
                    "color": pallete_colors[i if i < len(values) else i % len(values)]
                },
            )
            for i, value in enumerate(values)
        ]
    )


def to_line_stack(df, widget):
    if not widget.second_dimension:
        return to_line(df, widget)

    pallete_colors = get_pallete_colors(widget)
    return px.line(
        df,
        x=widget.dimension,
        y=_get_first_value_or_count(widget),
        markers=True,
        line_shape="spline",
        color=widget.second_dimension,
        color_discrete_sequence=pallete_colors,
    )


def to_column(df, widget, orientation="v"):
    values = get_metrics(widget)
    pallete_colors = get_pallete_colors(widget)

    fig = go.Figure(
        data=[
            go.Bar(
                name=value,
                x=df[widget.dimension] if orientation == "v" else df[value],
                y=df[value] if orientation == "v" else df[widget.dimension],
                orientation=orientation,
                marker={
                    "color": pallete_colors[i if i < len(values) else i % len(values)]
                },
            )
            for i, value in enumerate(values)
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
        x=widget.dimension if orientation == "v" else _get_first_value_or_count(widget),
        y=_get_first_value_or_count(widget) if orientation == "v" else widget.dimension,
        color=widget.second_dimension,
        orientation=orientation,
        color_discrete_sequence=get_pallete_colors(widget),
        color_continuous_scale=get_pallete_colors(widget),
    )


def to_pie(df, widget):
    return px.pie(
        df,
        names=widget.dimension,
        values=_get_first_value_or_count(widget),
        hole=0.3 if widget.kind == Widget.Kind.DONUT else None,
        color_discrete_sequence=get_pallete_colors(widget),
    )


def to_scatter(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    x, y = [unique_names.get(value, value.column) for value in aggregations][:2]

    return px.scatter(df, x=x, y=y, color_discrete_sequence=get_pallete_colors(widget))


def to_bubble(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    x, y, z = [unique_names.get(value, value.column) for value in aggregations][:3]
    return px.scatter(
        df, x=x, y=y, size=z, color_discrete_sequence=get_pallete_colors(widget)
    )


def pivot_df(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    return df.melt(
        value_vars=[unique_names.get(col, col.column) for col in aggregations]
    )


def to_radar(df, widget):
    df = pivot_df(df, widget)
    return px.line_polar(df, r="value", theta="variable", line_close=True)


def to_funnel(df, widget):
    df = pivot_df(df, widget)
    return px.funnel_area(
        df,
        names="variable",
        values="value",
        color_discrete_sequence=get_pallete_colors(widget),
    )


def to_area(df, widget):
    values = get_metrics(widget)
    pallete_colors = get_pallete_colors(widget)
    return go.Figure(
        data=[
            go.Scatter(
                name=value,
                x=df[widget.dimension],
                y=df[value],
                fill="tozeroy" if i == 0 else "tonexty",
                line={
                    "color": pallete_colors[i if i < len(values) else i % len(values)]
                },
            )
            for i, value in enumerate(values)
        ]
    )


def to_heatmap(df, widget):
    df = df.pivot(
        index=widget.dimension,
        columns=widget.second_dimension,
        values=_get_first_value_or_count(widget),
    )
    return px.imshow(df, color_continuous_scale=get_pallete_colors(widget))


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
            gauge={
                "axis": {"range": [min_val, max_val]},
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


CHARTS = {
    CombinationChart.Kind.LINE: go.Scatter,
    CombinationChart.Kind.AREA: partial(go.Scatter, fill="tozeroy"),
    CombinationChart.Kind.COLUMN: go.Bar,
}


def to_combo(df, widget):
    charts = widget.charts.all()
    unique_names = get_unique_column_names(charts, [widget.dimension])

    fig = make_subplots(
        specs=[[{"secondary_y": any(chart.on_secondary for chart in charts)}]]
    )
    pallete_colors = get_pallete_colors(widget)

    for i, chart in enumerate(charts):
        fig.add_trace(
            CHARTS[chart.kind](
                name=unique_names.get(chart, chart.column),
                x=df[widget.dimension],
                y=df[unique_names.get(chart, chart.column)],
                marker={
                    "color": pallete_colors[i if i < len(charts) else i % len(charts)]
                },
            ),
            secondary_y=chart.on_secondary,
        )
    return fig


def to_chart(df, widget):
    fig = CHART_FIG[widget.kind](df, widget)
    fig.layout.title = widget.name
    bg_color = (
        widget.background_color
        or widget.page.dashboard.widget_background_color
        or "#ffffff"
    )
    fig.layout.paper_bgcolor = bg_color
    fig.layout.plot_bgcolor = bg_color

    chart = fig.to_html(include_plotlyjs=False, config={"displayModeBar": False})
    chart_id = f"{widget.pk}-{uuid.uuid4()}"
    # Not sure whether there is a better solution for this but right now
    # It is necessary
    chart = chart.replace("div", 'div style="height:100%;"', 1)
    return chart, chart_id


CHART_FIG = {
    Widget.Kind.BUBBLE: to_bubble,
    Widget.Kind.HEATMAP: to_heatmap,
    Widget.Kind.SCATTER: to_scatter,
    Widget.Kind.RADAR: to_radar,
    Widget.Kind.FUNNEL: to_funnel,
    Widget.Kind.PIE: to_pie,
    Widget.Kind.DONUT: to_pie,
    Widget.Kind.COLUMN: to_column,
    Widget.Kind.STACKED_COLUMN: to_column_stack,
    Widget.Kind.BAR: partial(to_column, orientation="h"),
    Widget.Kind.STACKED_BAR: partial(to_column_stack, orientation="h"),
    Widget.Kind.AREA: to_area,
    Widget.Kind.LINE: to_line,
    Widget.Kind.STACKED_LINE: to_line_stack,
    Widget.Kind.COMBO: to_combo,
    Widget.Kind.GAUGE: to_gauge,
}
