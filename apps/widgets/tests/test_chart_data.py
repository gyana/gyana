import pandas as pd
import pytest

from apps.widgets.fusion.chart import CHART_DATA
from apps.widgets.models import Widget

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
AGGREGATION_1 = {"column": "medals", "function": "mean"}
AGGREGATION_2 = {"column": "points", "function": "sum"}
AGGREGATION_3 = {"column": "wins", "function": "count"}

SINGLE_VALUE_DATA = {
    "data": [
        {"label": label, "value": value} for label, value in zip(DIMENSION, range(10))
    ]
}

NO_AGGREGATION_DATA = {
    "data": [
        {"label": label, "value": value} for label, value in zip(DIMENSION, [2, 4] * 5)
    ]
}

MULTI_VALUE_DATA_COUNT = {
    "categories": [{"category": [{"label": label} for label in DIMENSION]}],
    "dataset": [{"data": [{"value": value} for value in [2, 4] * 5]}],
}

MULTI_VALUE_DATA_AGGREGATION = {
    "categories": [{"category": [{"label": label} for label in DIMENSION]}],
    "dataset": [{"data": [{"value": value} for value in range(10)]}],
}

MULTI_VALUE_DATA_MULTI = {
    "categories": [{"category": [{"label": label} for label in DIMENSION]}],
    "dataset": [
        {
            "seriesname": label,
            "data": [{"value": value} for value in iterator],
        }
        for label, iterator in [
            ("medals", range(10)),
            ("points", range(10, 20)),
        ]
    ],
}

TWO_DIMENSION_DF = pd.DataFrame(
    {
        "dimension": ["a"] * 5 + ["b"] * 5,
        "second_dimension": list(range(5)) * 2,
        "medals": range(10),
    }
)


STACK_DATA = {
    "categories": [{"category": [{"label": label} for label in ["a", "b"]]}],
    "dataset": [
        {"seriesname": str(color), "data": [{"value": value} for value in iterator]}
        for color, iterator in zip(range(5), zip(range(5), range(5, 10)))
    ],
}

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

COLORRANGE = {
    "colorrange": {
        "gradient": "0",
        "minvalue": "0",
        "code": "E24B1A",
        "color": [
            {"code": "0155E8", "minvalue": "0.0", "maxvalue": "1.2857142857142858"},
            {
                "code": "2BA8E8",
                "minvalue": "1.2857142857142858",
                "maxvalue": "2.5714285714285716",
            },
            {
                "code": "21C451",
                "minvalue": "2.5714285714285716",
                "maxvalue": "3.8571428571428577",
            },
            {
                "code": "FFD315",
                "minvalue": "3.8571428571428577",
                "maxvalue": "5.142857142857143",
            },
            {
                "code": "E8990C",
                "minvalue": "5.142857142857143",
                "maxvalue": "6.428571428571429",
            },
            {
                "code": "C24314",
                "minvalue": "6.428571428571429",
                "maxvalue": "7.714285714285715",
            },
            {"code": "FF0000", "minvalue": "7.714285714285715", "maxvalue": "9.0"},
        ],
    }
}

NO_DIMENSION_DF = pd.DataFrame({"medals": [10], "points": [20], "wins": [30]})


@pytest.mark.parametrize(
    "kind, df, aggregations, data_expected",
    [
        pytest.param(
            Widget.Kind.SCATTER,
            ONE_DIMENSION_DF,
            [
                AGGREGATION_1,
                AGGREGATION_2,
            ],
            {
                "dataset": [
                    {
                        "data": [
                            {"x": x, "y": y} for x, y in zip(range(10), range(10, 20))
                        ]
                    }
                ],
            },
            id="scatter",
        ),
        pytest.param(
            Widget.Kind.PIE,
            ONE_DIMENSION_DF[["dimension", "medals"]],
            [AGGREGATION_1],
            SINGLE_VALUE_DATA,
            id="pie",
        ),
        pytest.param(
            Widget.Kind.DONUT,
            ONE_DIMENSION_DF[["dimension", "medals"]],
            [AGGREGATION_1],
            SINGLE_VALUE_DATA,
            id="donut",
        ),
        pytest.param(
            Widget.Kind.PIE,
            ONE_DIMENSION_DF[["dimension", "count"]],
            [],
            NO_AGGREGATION_DATA,
            id="pie no aggregation",
        ),
        pytest.param(
            Widget.Kind.DONUT,
            ONE_DIMENSION_DF[["dimension", "count"]],
            [],
            NO_AGGREGATION_DATA,
            id="donut no aggregation",
        ),
        pytest.param(
            Widget.Kind.HEATMAP,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            {
                "dataset": [
                    {
                        "data": [
                            {"rowid": rowid, "columnid": str(columnid), "value": value}
                            for rowid, columnid, value in zip(
                                ["a"] * 5 + ["b"] * 5, list(range(5)) * 2, range(10)
                            )
                        ]
                    }
                ],
                **COLORRANGE,
            },
            id="heatmap",
        ),
        pytest.param(
            Widget.Kind.HEATMAP,
            TWO_DIMENSION_DF.rename(columns={"medals": "count"}),
            [],
            {
                "dataset": [
                    {
                        "data": [
                            {"rowid": rowid, "columnid": str(columnid), "value": value}
                            for rowid, columnid, value in zip(
                                ["a"] * 5 + ["b"] * 5, list(range(5)) * 2, range(10)
                            )
                        ]
                    }
                ],
                **COLORRANGE,
            },
            id="heatmap no aggregation",
        ),
        pytest.param(
            Widget.Kind.RADAR,
            NO_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, AGGREGATION_3],
            {
                "categories": [
                    {
                        "category": [
                            {"label": label} for label in ["medals", "points", "wins"]
                        ]
                    }
                ],
                "dataset": [{"data": [{"value": value} for value in [10, 20, 30]]}],
            },
            id="radar",
        ),
        pytest.param(
            Widget.Kind.FUNNEL,
            NO_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, AGGREGATION_3],
            {
                "data": [
                    {"label": label, "value": value}
                    for label, value in [("medals", 10), ("points", 20), ("wins", 30)]
                ]
            },
            id="funnel",
        ),
        pytest.param(
            Widget.Kind.PYRAMID,
            NO_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, AGGREGATION_3],
            {
                "data": [
                    {"label": label, "value": value}
                    for label, value in [
                        ("wins", 30),
                        ("points", 20),
                        ("medals", 10),
                    ]
                ]
            },
            id="pyramid",
        ),
        pytest.param(
            Widget.Kind.COLUMN,
            ONE_DIMENSION_DF,
            [],
            MULTI_VALUE_DATA_COUNT,
            id="column no aggregation",
        ),
        pytest.param(
            Widget.Kind.COLUMN,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            MULTI_VALUE_DATA_AGGREGATION,
            id="column one aggregation",
        ),
        pytest.param(
            Widget.Kind.COLUMN,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            MULTI_VALUE_DATA_MULTI,
            id="column two aggregations",
        ),
        pytest.param(
            Widget.Kind.BAR,
            ONE_DIMENSION_DF,
            [],
            MULTI_VALUE_DATA_COUNT,
            id="bar no aggregation",
        ),
        pytest.param(
            Widget.Kind.BAR,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            MULTI_VALUE_DATA_AGGREGATION,
            id="bar one aggregation",
        ),
        pytest.param(
            Widget.Kind.BAR,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            MULTI_VALUE_DATA_MULTI,
            id="bar two aggregations",
        ),
        pytest.param(
            Widget.Kind.LINE,
            ONE_DIMENSION_DF,
            [],
            MULTI_VALUE_DATA_COUNT,
            id="line no aggregation",
        ),
        pytest.param(
            Widget.Kind.LINE,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            MULTI_VALUE_DATA_AGGREGATION,
            id="line one aggregation",
        ),
        pytest.param(
            Widget.Kind.LINE,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            MULTI_VALUE_DATA_MULTI,
            id="line three aggregations",
        ),
        pytest.param(
            Widget.Kind.AREA,
            ONE_DIMENSION_DF,
            [],
            MULTI_VALUE_DATA_COUNT,
            id="area no aggregation",
        ),
        pytest.param(
            Widget.Kind.AREA,
            ONE_DIMENSION_DF,
            [AGGREGATION_1],
            MULTI_VALUE_DATA_AGGREGATION,
            id="area one aggregation",
        ),
        pytest.param(
            Widget.Kind.AREA,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2],
            MULTI_VALUE_DATA_MULTI,
            id="area three aggregations",
        ),
        pytest.param(
            Widget.Kind.STACKED_COLUMN,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            STACK_DATA,
            id="stacked column one aggregations and second dimension",
        ),
        pytest.param(
            Widget.Kind.STACKED_BAR,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            STACK_DATA,
            id="stacked bar one aggregations and second dimension",
        ),
        pytest.param(
            Widget.Kind.STACKED_LINE,
            TWO_DIMENSION_DF,
            [AGGREGATION_1],
            STACK_DATA,
            id="stacked line one aggregations and second dimension",
        ),
        pytest.param(
            Widget.Kind.BUBBLE,
            ONE_DIMENSION_DF,
            [AGGREGATION_1, AGGREGATION_2, {"column": "count", "function": "count"}],
            {
                "categories": [
                    {"category": [{"label": str(label)} for label in range(10)]}
                ],
                "dataset": [
                    {
                        "data": [
                            {"x": x, "y": y, "z": z, "id": i}
                            for x, y, z, i in zip(
                                range(10), range(10, 20), [2, 4] * 5, DIMENSION
                            )
                        ]
                    }
                ],
            },
            id="bubble",
        ),
    ],
)
def test_chart_data(widget_factory, kind, df, aggregations, data_expected):
    widget = widget_factory(
        kind=kind, dimension="dimension", second_dimension="second_dimension"
    )
    for aggregation in aggregations:
        widget.aggregations.create(**aggregation)
    data = CHART_DATA[widget.kind](widget, df)

    assert data == data_expected


def test_chart_combo_data(widget_factory):
    widget = widget_factory(kind=Widget.Kind.COMBO, dimension="dimension")
    widget.charts.create(**AGGREGATION_1)
    widget.charts.create(**AGGREGATION_2, kind="line", on_secondary=True)
    data = CHART_DATA[widget.kind](widget, ONE_DIMENSION_DF)
    assert data == COMBO_DATA
