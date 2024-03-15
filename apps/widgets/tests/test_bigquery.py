import pytest

from apps.widgets.engine import get_query_from_widget
from apps.widgets.models import NO_DIMENSION_WIDGETS, Widget
from apps.widgets.visuals import pre_filter

pytestmark = pytest.mark.django_db


SINGLE_DIMENSION_QUERY = """\
SELECT
  t0.*
FROM (
  SELECT
    t1.`is_nice`,
    count(1) AS `count`
  FROM `project.dataset`.table AS t1
  GROUP BY
    1
) AS t0
ORDER BY
  t0.`is_nice` ASC\
"""

SINGLE_DIMENSION_SINGLE_AGGREGATION_QUERY = SINGLE_DIMENSION_QUERY.replace(
    "count(1) AS `count`", "sum(t1.`stars`) AS `stars`"
)
SINGLE_DIMENSION_TWO_AGGREGATIONS_QUERY = SINGLE_DIMENSION_QUERY.replace(
    "count(1) AS `count`",
    "sum(t1.`stars`) AS `stars`,\n    count(t1.`athlete`) AS `athlete`",
)

TWO_DIMENSION_QUERY = """\
SELECT
  t0.*
FROM (
  SELECT
    t1.`is_nice`,
    t1.`medals`,
    count(1) AS `count`
  FROM `project.dataset`.table AS t1
  GROUP BY
    1,
    2
) AS t0
ORDER BY
  t0.`is_nice` ASC\
"""

TWO_DIMENSION_SINGLE_AGGREGATION_QUERY = TWO_DIMENSION_QUERY.replace(
    "count(1) AS `count`", "sum(t1.`stars`) AS `stars`"
)

NO_DIMENSION_THREE_AGGREGATIONS_QUERY = """\
SELECT
  sum(t0.`stars`) AS `stars`,
  count(t0.`athlete`) AS `athlete`,
  avg(t0.`id`) AS `id`
FROM `project.dataset`.table AS t0\
"""

simple_params = pytest.mark.parametrize(
    "kind",
    [
        pytest.param(Widget.Kind.COLUMN, id="column"),
        pytest.param(Widget.Kind.STACKED_COLUMN, id="stacked column"),
        pytest.param(Widget.Kind.BAR, id="bar"),
        pytest.param(Widget.Kind.STACKED_BAR, id="stacked bar"),
        pytest.param(Widget.Kind.LINE, id="line"),
        pytest.param(Widget.Kind.STACKED_LINE, id="stacked line"),
        pytest.param(Widget.Kind.AREA, id="area"),
        pytest.param(Widget.Kind.PIE, id="pie"),
        pytest.param(Widget.Kind.DONUT, id="donut"),
        # Scatter actually requires two aggregations but the query still compiles
        # this should be enforced in the form
        pytest.param(Widget.Kind.SCATTER, id="scatter"),
    ],
)


@simple_params
def test_only_one_dimension(kind, mock_bigquery, widget_factory):
    widget = widget_factory(kind=kind, dimension="is_nice")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == SINGLE_DIMENSION_QUERY


@simple_params
def test_one_dimension_one_aggregation(kind, mock_bigquery, widget_factory):
    widget = widget_factory(kind=kind, dimension="is_nice")
    widget.aggregations.create(column="stars", function="sum")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == SINGLE_DIMENSION_SINGLE_AGGREGATION_QUERY


@simple_params
def test_one_dimension_two_aggregations(kind, mock_bigquery, widget_factory):
    widget = widget_factory(kind=kind, dimension="is_nice")
    widget.aggregations.create(column="stars", function="sum")
    widget.aggregations.create(column="athlete", function="count")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == SINGLE_DIMENSION_TWO_AGGREGATIONS_QUERY


stacked_params = pytest.mark.parametrize(
    "kind",
    [
        pytest.param(Widget.Kind.STACKED_COLUMN, id="stacked column"),
        pytest.param(Widget.Kind.STACKED_BAR, id="stacked bar"),
        pytest.param(Widget.Kind.STACKED_LINE, id="stacked line"),
        pytest.param(Widget.Kind.HEATMAP, id="heatmap"),
    ],
)


@stacked_params
def test_two_dimension(kind, mock_bigquery, widget_factory):
    widget = widget_factory(kind=kind, dimension="is_nice", second_dimension="medals")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == TWO_DIMENSION_QUERY


@stacked_params
def test_two_dimension_one_aggregation(kind, mock_bigquery, widget_factory):
    widget = widget_factory(kind=kind, dimension="is_nice", second_dimension="medals")
    widget.aggregations.create(column="stars", function="sum")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == TWO_DIMENSION_SINGLE_AGGREGATION_QUERY


@pytest.mark.parametrize(
    "kind", [pytest.param(kind, id=kind) for kind in NO_DIMENSION_WIDGETS]
)
def test_no_dimension(kind, mock_bigquery, widget_factory):
    widget = widget_factory(kind=kind)
    widget.aggregations.create(column="stars", function="sum")
    widget.aggregations.create(column="athlete", function="count")
    widget.aggregations.create(column="id", function="mean")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == NO_DIMENSION_THREE_AGGREGATIONS_QUERY


def test_combo_chart(mock_bigquery, widget_factory):
    widget = widget_factory(kind=Widget.Kind.COMBO, dimension="is_nice")
    widget.charts.create(column="stars", function="sum")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.compile() == SINGLE_DIMENSION_SINGLE_AGGREGATION_QUERY
    widget.charts.create(column="athlete", function="count")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    # TODO: Weird issue where the backticks are removed by ibis
    assert query.compile() == SINGLE_DIMENSION_TWO_AGGREGATIONS_QUERY
