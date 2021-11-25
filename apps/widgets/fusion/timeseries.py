import json
import uuid
from functools import partial

from apps.widgets.models import COUNT_COLUMN_NAME, Widget

from .fusioncharts import FusionCharts, FusionTable, TimeSeries
from .utils import DEFAULT_HEIGHT, DEFAULT_WIDTH

TYPE_TO_FORMAT = {
    "Timestamp": "%Y-%m-%dT%H:%M:%S",
    "Date": "%Y-%m-%d",
    "Time": "%H:%M:%S",
}


def parse_dimension(query, df, dimension):
    dimension_format = TYPE_TO_FORMAT[query.schema()[dimension].name]
    return dimension_format, [
        value.strftime(dimension_format) for value in df[dimension].to_list()
    ]


def to_multivariate(type_, widget, df, query):
    aggregations = widget.aggregations.all()
    dimension_format, dimension = parse_dimension(query, df, widget.dimension)
    metrics = [col.column for col in aggregations] or [COUNT_COLUMN_NAME]
    schema = [
        {"name": widget.dimension, "type": "date", "format": dimension_format},
        *[{"name": col, "type": "number"} for col in metrics],
    ]

    data = [
        list(row)
        for row in zip(dimension, *[df[metric].to_list() for metric in metrics])
    ]
    fusiontable = FusionTable(schema, data)
    timeseries = TimeSeries(fusiontable)
    timeseries.AddAttribute(
        "yAxis",
        json.dumps([{"plot": {"value": metric, "type": type_}} for metric in metrics]),
    )
    return timeseries


def to_stack(type_, widget, df, query):
    dimension_format, dimension = parse_dimension(query, df, widget.dimension)

    aggregation = widget.aggregations.first()
    metric = aggregation.column if aggregation else COUNT_COLUMN_NAME
    schema = [
        {"name": widget.second_dimension, "type": "string"},
        {"name": widget.dimension, "type": "date", "format": dimension_format},
        {"name": metric, "type": "number"},
    ]
    data = [
        list(row)
        for row in zip(
            df[widget.second_dimension].astype(str).to_list(),
            dimension,
            df[metric].to_list(),
        )
    ]
    fusiontable = FusionTable(schema, data)
    timeseries = TimeSeries(fusiontable)
    timeseries.AddAttribute(
        "yAxis", json.dumps([{"plot": {"value": metric, "type": type_}}])
    ),
    timeseries.AddAttribute("series", f'"{widget.second_dimension}"')
    return timeseries


def to_timeseries(widget, df, query):
    timeseries = TIMESERIES_DATA[widget.kind](widget, df, query)
    chart_id = f"{widget.pk}-{uuid.uuid4()}"

    timeseries.AddAttribute("styleDefinition", json.dumps({"bg": {"fill-opacity": 0}}))
    timeseries.AddAttribute("navigator", json.dumps({"enabled": 0}))
    timeseries.AddAttribute(
        "extensions",
        json.dumps(
            {
                "standardRangeSelector": {"enabled": "0"},
                "customRangeSelector": {"enabled": "0"},
            }
        ),
    )

    timeseries.AddAttribute(
        "chart",
        json.dumps(
            {
                "theme": "fusion, CustomDashboardTheme",
                "paletteColors": ",".join(widget.dashboard.palette_colors),
                "style": {
                    "background": "bg",
                    "canvas": "bg",
                },
            }
        ),
    )

    chart = FusionCharts(
        "timeseries",
        f"chart-{chart_id}",
        DEFAULT_WIDTH,
        DEFAULT_HEIGHT,
        f"chart-{chart_id}-container",
        "json",
        timeseries,
    )

    return chart, chart_id


TIMESERIES_DATA = {
    Widget.Kind.TIMESERIES_LINE: partial(to_multivariate, "line"),
    Widget.Kind.TIMESERIES_COLUMN: partial(to_multivariate, "column"),
    Widget.Kind.TIMESERIES_AREA: partial(to_multivariate, "area"),
    Widget.Kind.TIMESERIES_STACKED_LINE: partial(to_stack, "line"),
    Widget.Kind.TIMESERIES_STACKED_COLUMN: partial(to_stack, "column"),
}
