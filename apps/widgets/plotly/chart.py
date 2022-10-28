import uuid

import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from apps.widgets.fusion.chart import _get_first_value_or_count, get_unique_column_names
from apps.widgets.models import COUNT_COLUMN_NAME


def to_stack(df, widget):
    if not widget.second_dimension:
        return to_line(df, widget)
    fig = go.Figure(
        data=[
            go.Scatter(
                x=group[widget.dimension],
                y=group[_get_first_value_or_count(widget)],
                mode="lines+markers",
                line_shape="spline",
                name=name,
            )
            for name, group in df.groupby(widget.second_dimension)
        ],
        layout=go.Layout(
            title=widget.name,
        ),
    )

    chart = plot(fig, output_type="div", include_plotlyjs=False)
    chart_id = f"{widget.pk}-{uuid.uuid4()}"

    return chart, chart_id


def to_line(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    values = [unique_names.get(value, value.column) for value in aggregations] or [
        COUNT_COLUMN_NAME
    ]
    fig = go.Figure(
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

    chart = plot(fig, output_type="div", include_plotlyjs=False)
    chart_id = f"{widget.pk}-{uuid.uuid4()}"

    return chart, chart_id


def to_bar(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    values = [unique_names.get(value, value.column) for value in aggregations] or [
        COUNT_COLUMN_NAME
    ]

    fig = go.Figure(
        data=[
            go.Bar(name=value, x=df[widget.dimension], y=df[value]) for value in values
        ]
    )
    # Change the bar mode
    fig.update_layout(barmode="group")
    chart = plot(fig, output_type="div", include_plotlyjs=False)
    chart_id = f"{widget.pk}-{uuid.uuid4()}"

    return chart, chart_id
