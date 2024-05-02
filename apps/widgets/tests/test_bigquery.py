import ibis
import pytest

from apps.widgets.engine import get_query_from_widget
from apps.widgets.models import NO_DIMENSION_WIDGETS, Widget
from apps.widgets.visuals import pre_filter

pytestmark = pytest.mark.django_db

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
def test_only_one_dimension(kind, widget_factory, engine):
    widget = widget_factory(kind=kind, dimension="is_nice")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by("is_nice")
        .aggregate(count=ibis._.count())
        .order_by("is_nice")
    )


@simple_params
def test_one_dimension_one_aggregation(kind, widget_factory, engine):
    widget = widget_factory(kind=kind, dimension="is_nice")
    widget.aggregations.create(column="stars", function="sum")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by("is_nice")
        .aggregate(stars=engine.data.stars.sum())
        .order_by("is_nice")
    )


@simple_params
def test_one_dimension_two_aggregations(kind, widget_factory, engine):
    widget = widget_factory(kind=kind, dimension="is_nice")
    widget.aggregations.create(column="stars", function="sum")
    widget.aggregations.create(column="athlete", function="count")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by("is_nice")
        .aggregate(stars=engine.data.stars.sum(), athlete=engine.data.athlete.count())
        .order_by("is_nice")
    )


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
def test_two_dimension(kind, widget_factory, engine):
    widget = widget_factory(kind=kind, dimension="is_nice", second_dimension="medals")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by(["is_nice", "medals"])
        .aggregate(count=ibis._.count())
        .order_by("is_nice")
    )


@stacked_params
def test_two_dimension_one_aggregation(kind, widget_factory, engine):
    widget = widget_factory(kind=kind, dimension="is_nice", second_dimension="medals")
    widget.aggregations.create(column="stars", function="sum")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by(["is_nice", "medals"])
        .aggregate(stars=engine.data.stars.sum())
        .order_by("is_nice")
    )


@pytest.mark.parametrize(
    "kind", [pytest.param(kind, id=kind) for kind in NO_DIMENSION_WIDGETS]
)
def test_no_dimension(kind, widget_factory, engine):
    widget = widget_factory(kind=kind)
    widget.aggregations.create(column="stars", function="sum")
    widget.aggregations.create(column="athlete", function="count")
    widget.aggregations.create(column="id", function="mean")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.aggregate(
            stars=engine.data.stars.sum(),
            athlete=engine.data.athlete.count(),
            id=engine.data.id.mean(),
        )
    )


def test_combo_chart(widget_factory, engine):
    widget = widget_factory(kind=Widget.Kind.COMBO, dimension="is_nice")
    widget.charts.create(column="stars", function="sum")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by("is_nice")
        .aggregate(stars=engine.data.stars.sum())
        .order_by("is_nice")
    )

    widget.charts.create(column="athlete", function="count")
    query = get_query_from_widget(widget, pre_filter(widget, None))

    assert query.equals(
        engine.data.group_by("is_nice")
        .aggregate(stars=engine.data.stars.sum(), athlete=engine.data.athlete.count())
        .order_by("is_nice")
    )
