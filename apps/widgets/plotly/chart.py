import uuid

import plotly.graph_objects as go
from plotly.offline import plot

from apps.widgets.fusion.chart import get_unique_column_names
from apps.widgets.models import COUNT_COLUMN_NAME


def to_line(df, widget):
    aggregations = widget.aggregations.all()
    unique_names = get_unique_column_names(aggregations, [widget.dimension])
    values = [unique_names.get(value, value.column) for value in aggregations] or [
        COUNT_COLUMN_NAME
    ]
    fig = go.Figure(
        data=[
            go.Scatter(x=df[widget.dimension], y=df[value], mode="lines", name=value)
            for value in values
        ],
        layout=go.Layout(
            title=widget.name,
        ),
    )

    chart = plot(fig, output_type="div", include_plotlyjs=False)
    chart_id = f"{widget.pk}-{uuid.uuid4()}"

    return chart, chart_id
