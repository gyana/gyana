import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal

from apps.widgets.models import Widget
from apps.widgets.plotly.chart import CHART_FIG

pytestmark = pytest.mark.django_db

DIMENSION = list("abcdefghij")
ONE_DIMENSION_DF = pd.DataFrame(
    {
        "dimension": DIMENSION,
        "medals": range(10),
        "points": range(10, 20),
        "count": [2, 4] * 5,
    }
)
AGGREGATION_1 = {"column": "medals", "function": "mean", "sort_index": 2}
AGGREGATION_2 = {"column": "points", "function": "sum", "sort_index": 1}
AGGREGATION_3 = {"column": "wins", "function": "count", "sort_index": 0}


TWO_DIMENSION_DF = pd.DataFrame(
    {
        "dimension": ["a"] * 5 + ["b"] * 5,
        "second_dimension": list(range(5)) * 2,
        "medals": range(10),
    }
)


COMBO_DATA = {
    "categories": [{"category": [{"label": label} for label in DIMENSION]}],
    "dataset": [
        {
            "seriesname": "medals",
            "renderAs": "column",
            "parentYAxis": "P",
            "data": [{"value": value} for value in range(10)],
        },
        {
            "seriesname": "points",
            "renderAs": "line",
            "parentYAxis": "S",
            "data": [{"value": value} for value in range(10, 20)],
        },
    ],
}


NO_DIMENSION_DF = pd.DataFrame({"medals": [10], "points": [20], "wins": [30]})


@pytest.mark.parametrize(
    "kind, df, aggregations, chart_type, data_expected",
    [
        pytest.param(
            Widget.Kind.SCATTER,
            ONE_DIMENSION_DF,
            [
                AGGREGATION_1,
                AGGREGATION_2,
            ],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.medals,
                    "y": ONE_DIMENSION_DF.points,
                    "mode": "markers",
                }
            ],
            id="scatter",
        ),
        pytest.param(
            Widget.Kind.PIE,
            ONE_DIMENSION_DF[["dimension", "medals"]],
            [AGGREGATION_1],
            "pie",
            [{"labels": ONE_DIMENSION_DF.dimension, "values": ONE_DIMENSION_DF.medals}],
            id="pie",
        ),
        pytest.param(
            Widget.Kind.DONUT,
            ONE_DIMENSION_DF[["dimension", "medals"]],
            [AGGREGATION_1],
            "pie",
            [
                {
                    "labels": ONE_DIMENSION_DF.dimension,
                    "values": ONE_DIMENSION_DF.medals,
                    "hole": 0.3,
                }
            ],
            id="donut",
        ),
        pytest.param(
            Widget.Kind.PIE,
            ONE_DIMENSION_DF[["dimension", "count"]],
            [],
            "pie",
            [
                {
                    "labels": ONE_DIMENSION_DF.dimension,
                    "values": ONE_DIMENSION_DF["count"],
                }
            ],
            id="pie no aggregation",
        ),
        pytest.param(
            Widget.Kind.DONUT,
            ONE_DIMENSION_DF[["dimension", "count"]],
            [],
            "pie",
            [
                {
                    "labels": ONE_DIMENSION_DF.dimension,
                    "values": ONE_DIMENSION_DF["count"],
                    "hole": 0.3,
                }
            ],
            id="donut no aggregation",
        ),
        pytest.param(
            Widget.Kind.HEATMAP,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            "heatmap",
            [
                {
                    "x": pd.Series(range(5)),
                    "y": pd.Series(["a", "b"]),
                    "z": np.array(range(10)).reshape((2, 5)),
                }
            ],
            id="heatmap",
        ),
        pytest.param(
            Widget.Kind.HEATMAP,
            TWO_DIMENSION_DF.rename(columns={"medals": "count"}),
            [],
            "heatmap",
            [
                {
                    "x": pd.Series(range(5)),
                    "y": pd.Series(["a", "b"]),
                    "z": np.array(range(10)).reshape((2, 5)),
                }
            ],
            id="heatmap no aggregation",
        ),
        pytest.param(
            Widget.Kind.RADAR,
            NO_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, AGGREGATION_3],
            "scatterpolar",
            [
                {
                    "theta": np.array(["medals", "points", "wins", "medals"]),
                    "r": np.array([10, 20, 30, 10]),
                    "mode": "lines",
                }
            ],
            id="radar",
        ),
        pytest.param(
            Widget.Kind.FUNNEL,
            NO_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, AGGREGATION_3],
            "funnelarea",
            [
                {
                    "labels": np.array(["medals", "points", "wins"]),
                    "values": np.array([10, 20, 30]),
                }
            ],
            id="funnel",
        ),
        pytest.param(
            Widget.Kind.COLUMN,
            ONE_DIMENSION_DF,
            [],
            "bar",
            [
                {
                    "orientation": "v",
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF["count"],
                }
            ],
            id="column no aggregation",
        ),
        pytest.param(
            Widget.Kind.COLUMN,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            "bar",
            [
                {
                    "orientation": "v",
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.medals,
                }
            ],
            id="column one aggregation",
        ),
        pytest.param(
            Widget.Kind.COLUMN,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            "bar",
            [
                {
                    "orientation": "v",
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.medals,
                },
                {"x": ONE_DIMENSION_DF.dimension, "y": ONE_DIMENSION_DF.points},
            ],
            id="column two aggregations",
        ),
        pytest.param(
            Widget.Kind.BAR,
            ONE_DIMENSION_DF,
            [],
            "bar",
            [
                {
                    "orientation": "h",
                    "y": ONE_DIMENSION_DF.dimension,
                    "x": ONE_DIMENSION_DF["count"],
                }
            ],
            id="bar no aggregation",
        ),
        pytest.param(
            Widget.Kind.BAR,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            "bar",
            [
                {
                    "orientation": "h",
                    "y": ONE_DIMENSION_DF.dimension,
                    "x": ONE_DIMENSION_DF.medals,
                }
            ],
            id="bar one aggregation",
        ),
        pytest.param(
            Widget.Kind.BAR,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            "bar",
            [
                {
                    "orientation": "h",
                    "y": ONE_DIMENSION_DF.dimension,
                    "x": ONE_DIMENSION_DF.medals,
                },
                {
                    "y": ONE_DIMENSION_DF.dimension,
                    "x": ONE_DIMENSION_DF.points,
                },
            ],
            id="bar two aggregations",
        ),
        pytest.param(
            Widget.Kind.LINE,
            ONE_DIMENSION_DF,
            [],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF["count"],
                    "mode": "lines+markers",
                }
            ],
            id="line no aggregation",
        ),
        pytest.param(
            Widget.Kind.LINE,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.medals,
                    "mode": "lines+markers",
                }
            ],
            id="line one aggregation",
        ),
        pytest.param(
            Widget.Kind.LINE,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.medals,
                    "mode": "lines+markers",
                },
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.points,
                    "mode": "lines+markers",
                },
            ],
            id="line two aggregations",
        ),
        pytest.param(
            Widget.Kind.AREA,
            ONE_DIMENSION_DF,
            [],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF["count"],
                    "fill": "tozeroy",
                }
            ],
            id="area no aggregation",
        ),
        pytest.param(
            Widget.Kind.AREA,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.medals,
                    "fill": "tozeroy",
                }
            ],
            id="area one aggregation",
        ),
        pytest.param(
            Widget.Kind.AREA,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.medals,
                    "fill": "tozeroy",
                },
                {
                    "x": ONE_DIMENSION_DF.dimension,
                    "y": ONE_DIMENSION_DF.points,
                    "fill": "tonexty",
                },
            ],
            id="area two aggregations",
        ),
        pytest.param(
            Widget.Kind.STACKED_COLUMN,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            "bar",
            [
                {
                    "orientation": "v",
                    "x": TWO_DIMENSION_DF.dimension,
                    "y": TWO_DIMENSION_DF.medals,
                    "marker": {"color": TWO_DIMENSION_DF.second_dimension},
                }
            ],
            id="stacked column one aggregations and second dimension",
        ),
        pytest.param(
            Widget.Kind.STACKED_BAR,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            "bar",
            [
                {
                    "orientation": "h",
                    "y": TWO_DIMENSION_DF.dimension,
                    "x": TWO_DIMENSION_DF.medals,
                    "marker": {"color": TWO_DIMENSION_DF.second_dimension},
                }
            ],
            id="stacked bar one aggregations and second dimension",
        ),
        pytest.param(
            Widget.Kind.STACKED_LINE,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            "scatter",
            [
                {
                    "x": np.array(["a", "b"]),
                    "y": np.array([0, 5]),
                },
                {"y": np.array([1, 6])},
                {"y": np.array([2, 7])},
                {"y": np.array([3, 8])},
                {"y": np.array([4, 9])},
            ],
            id="stacked line one aggregations and second dimension",
        ),
        pytest.param(
            Widget.Kind.BUBBLE,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, {"column": "count", "function": "count"}],
            "scatter",
            [
                {
                    "x": ONE_DIMENSION_DF.medals,
                    "y": ONE_DIMENSION_DF.points,
                    "mode": "markers",
                    "marker": {"size": ONE_DIMENSION_DF["count"]},
                }
            ],
            id="bubble",
        ),
    ],
)
def test_chart(widget_factory, kind, df, aggregations, chart_type, data_expected):
    widget = widget_factory(
        kind=kind, dimension="dimension", second_dimension="second_dimension"
    )
    for aggregation in aggregations:
        widget.aggregations.create(**aggregation)
    traces = CHART_FIG[widget.kind](df, widget).data

    assert traces[0].type == chart_type
    for i, d in enumerate(data_expected):
        data = traces[i]
        for key, item in d.items():
            assert_item(data, item, key)


def assert_item(data, item, key):
    if isinstance(item, dict):
        for k, i in item.items():
            assert_item(data[key], i, k)
    elif isinstance(item, (pd.Series, np.ndarray)):
        assert_array_equal(data[key], item)
    else:
        assert data[key] == item


def test_chart_combo(widget_factory):
    widget = widget_factory(kind=Widget.Kind.COMBO, dimension="dimension")
    widget.charts.create(
        column=AGGREGATION_1["column"], function=AGGREGATION_1["function"]
    )
    widget.charts.create(
        column=AGGREGATION_2["column"],
        function=AGGREGATION_2["function"],
        kind="line",
        on_secondary=True,
    )
    data = CHART_FIG[widget.kind](ONE_DIMENSION_DF, widget).data
    assert len(data) == 2

    column_chart = data[0]
    assert column_chart.type == "bar"
    assert_array_equal(column_chart.x, ONE_DIMENSION_DF.dimension)
    assert_array_equal(column_chart.y, ONE_DIMENSION_DF.medals)

    line_chart = data[1]
    assert line_chart.type == "scatter"
    assert line_chart.yaxis == "y2"
    assert_array_equal(line_chart.x, ONE_DIMENSION_DF.dimension)
    assert_array_equal(line_chart.y, ONE_DIMENSION_DF.points)
