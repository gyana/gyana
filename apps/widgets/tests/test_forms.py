import pytest

from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.widgets.forms import FORMS
from apps.widgets.formsets import (
    AggregationColumnFormset,
    CombinationChartFormset,
    FilterFormset,
    Min2Formset,
    Min3Formset,
    OptionalMetricFormset,
    SingleMetricFormset,
    XYMetricFormset,
    XYZMetricFormset,
)
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(
    bigquery,
    project,
    dashboard_factory,
    integration_table_factory,
):
    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    return dashboard_factory(project=project), integration_table_factory(
        project=project
    )


@pytest.mark.parametrize(
    "kind, formset_classes",
    [
        pytest.param(Widget.Kind.TABLE, {FilterFormset}, id="table"),
        pytest.param(Widget.Kind.FUNNEL, {FilterFormset, Min2Formset}, id="funnel"),
        pytest.param(Widget.Kind.PYRAMID, {FilterFormset, Min2Formset}, id="pyramid"),
        pytest.param(Widget.Kind.RADAR, {FilterFormset, Min3Formset}, id="radar"),
        pytest.param(
            Widget.Kind.METRIC, {FilterFormset, SingleMetricFormset}, id="metric"
        ),
    ],
)
def test_generic_form(kind, formset_classes, setup, widget_factory):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, dashboard=dashboard)
    form = FORMS[kind](instance=widget)

    assert set(form.get_live_fields()) == {"kind", "table"}
    assert set(form.get_live_formsets()) == formset_classes


@pytest.mark.parametrize(
    "kind, formset_classes",
    [
        pytest.param(
            Widget.Kind.BAR, {FilterFormset, AggregationColumnFormset}, id="bar"
        ),
        pytest.param(
            Widget.Kind.COLUMN, {FilterFormset, AggregationColumnFormset}, id="column"
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_COLUMN,
            {FilterFormset, AggregationColumnFormset},
            id="timeseries column",
        ),
        pytest.param(
            Widget.Kind.LINE, {FilterFormset, AggregationColumnFormset}, id="line"
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_LINE,
            {FilterFormset, AggregationColumnFormset},
            id="timeseries line",
        ),
        pytest.param(Widget.Kind.PIE, {FilterFormset, OptionalMetricFormset}, id="pie"),
        pytest.param(
            Widget.Kind.AREA, {FilterFormset, AggregationColumnFormset}, id="area"
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_AREA,
            {FilterFormset, AggregationColumnFormset},
            id="timeseries area",
        ),
        pytest.param(
            Widget.Kind.DONUT, {FilterFormset, AggregationColumnFormset}, id="donut"
        ),
        pytest.param(
            Widget.Kind.SCATTER, {FilterFormset, XYMetricFormset}, id="scatter"
        ),
        pytest.param(
            Widget.Kind.BUBBLE, {FilterFormset, XYZMetricFormset}, id="bubble"
        ),
        pytest.param(
            Widget.Kind.COMBO, {FilterFormset, CombinationChartFormset}, id="combo"
        ),
    ],
)
def test_one_dimension_form(kind, formset_classes, setup, widget_factory):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, dashboard=dashboard)
    form = FORMS[kind](instance=widget)

    if kind == Widget.Kind.COMBO:
        assert set(form.get_live_fields()) == {
            "kind",
            "table",
            "dimension",
        }
    else:
        assert set(form.get_live_fields()) == {
            "kind",
            "table",
            "sort_by",
            "sort_ascending",
            "dimension",
        }
    assert set(form.get_live_formsets()) == formset_classes
    assertFormChoicesLength(form, "dimension", 9)


@pytest.mark.parametrize(
    "kind, formset_classes",
    [
        pytest.param(
            Widget.Kind.HEATMAP, {FilterFormset, OptionalMetricFormset}, id="heatmap"
        ),
        pytest.param(
            Widget.Kind.STACKED_COLUMN,
            {FilterFormset, OptionalMetricFormset},
            id="stacked column",
        ),
        pytest.param(
            Widget.Kind.STACKED_BAR,
            {FilterFormset, OptionalMetricFormset},
            id="stacked bar",
        ),
        pytest.param(
            Widget.Kind.STACKED_LINE,
            {FilterFormset, AggregationColumnFormset},
            id="stacked line",
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_STACKED_COLUMN,
            {FilterFormset, AggregationColumnFormset},
            id="timeseries stacked column",
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_STACKED_LINE,
            {FilterFormset, AggregationColumnFormset},
            id="timeseries stacked line",
        ),
    ],
)
def test_two_dimension_form(kind, formset_classes, setup, widget_factory):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, dashboard=dashboard)
    form = FORMS[kind](instance=widget)

    fields = {"kind", "table", "dimension", "second_dimension"}
    if kind not in [Widget.Kind.STACKED_LINE, Widget.Kind.HEATMAP]:
        fields |= {"stack_100_percent"}

    assert set(form.get_live_fields()) == fields
    assert set(form.get_live_formsets()) == formset_classes
    assertFormChoicesLength(form, "dimension", 9)
    assertFormChoicesLength(form, "second_dimension", 9)
