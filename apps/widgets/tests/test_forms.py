import pytest

from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.widgets.forms import FORMS, WidgetSourceForm
from apps.widgets.formsets import (
    AggregationColumnFormset,
    AggregationWithFormattingFormset,
    ColumnFormset,
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

# Number is columns plus unselected option
NUM_COLUMN_OPTIONS = len(TABLE.schema()) + 1


@pytest.fixture
def setup(
    bigquery,
    project,
    dashboard_factory,
    integration_table_factory,
):
    mock_bq_client_with_schema(
        bigquery, [(name, str(type_)) for name, type_ in TABLE.schema().items()]
    )
    return dashboard_factory(project=project), integration_table_factory(
        project=project
    )


@pytest.mark.parametrize(
    "kind, formset_classes",
    [
        pytest.param(
            Widget.Kind.TABLE,
            {FilterFormset, ColumnFormset, AggregationWithFormattingFormset},
            id="table",
        ),
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
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = FORMS[kind](instance=widget, schema=TABLE.schema())
    fields = {"kind", "date_column"}
    if kind == Widget.Kind.TABLE:
        fields |= {"show_summary_row", "sort_column", "sort_ascending"}
    assert set(form.get_live_fields()) == fields
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
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = FORMS[kind](instance=widget)

    if kind == Widget.Kind.COMBO:
        assert set(form.get_live_fields()) == {
            "kind",
            "dimension",
            "date_column",
        }
    else:
        assert set(form.get_live_fields()) == {
            "kind",
            "dimension",
            "date_column",
        }
    assert set(form.get_live_formsets()) == formset_classes
    assertFormChoicesLength(form, "dimension", NUM_COLUMN_OPTIONS)


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
            {FilterFormset, OptionalMetricFormset},
            id="stacked line",
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_STACKED_COLUMN,
            {FilterFormset, OptionalMetricFormset},
            id="timeseries stacked column",
        ),
        pytest.param(
            Widget.Kind.TIMESERIES_STACKED_LINE,
            {FilterFormset, OptionalMetricFormset},
            id="timeseries stacked line",
        ),
    ],
)
def test_two_dimension_form(kind, formset_classes, setup, widget_factory):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = FORMS[kind](instance=widget)

    fields = {"kind", "dimension", "second_dimension", "date_column"}
    if kind not in [Widget.Kind.STACKED_LINE, Widget.Kind.HEATMAP]:
        fields |= {"stack_100_percent"}

    assert set(form.get_live_fields()) == fields
    assert set(form.get_live_formsets()) == formset_classes
    assertFormChoicesLength(form, "dimension", NUM_COLUMN_OPTIONS)
    assertFormChoicesLength(form, "second_dimension", NUM_COLUMN_OPTIONS)


def test_widget_source_form(setup, widget_factory):
    dashboard, table = setup
    widget = widget_factory(
        kind=Widget.Kind.TABLE, table=table, page__dashboard=dashboard
    )

    form = WidgetSourceForm(instance=widget)
    assert set(form.fields) == {"table", "search"}
    assertFormChoicesLength(form, "table", 2)
