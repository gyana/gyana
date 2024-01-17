import pytest

from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.widgets.forms import FORMS, GenericWidgetForm, WidgetSourceForm
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
            Widget.Kind.LINE, {FilterFormset, AggregationColumnFormset}, id="line"
        ),
        pytest.param(Widget.Kind.PIE, {FilterFormset, OptionalMetricFormset}, id="pie"),
        pytest.param(
            Widget.Kind.AREA, {FilterFormset, AggregationColumnFormset}, id="area"
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


@pytest.mark.parametrize(
    "kind, fields, formsets",
    [
        (Widget.Kind.METRIC, set(), {"single_metric"}),
        (
            Widget.Kind.TABLE,
            {"sort_column", "sort_ascending", "show_summary_row"},
            {"dimensions", "metrics"},
        ),
        (
            Widget.Kind.COLUMN,
            {"dimension", "sort_column", "sort_ascending"},
            {"default_metrics"},
        ),
        (
            Widget.Kind.STACKED_COLUMN,
            {
                "dimension",
                "sort_column",
                "sort_ascending",
                "second_dimension",
                "stack_100_percent",
            },
            {"optional_metrics"},
        ),
        (
            Widget.Kind.BAR,
            {"dimension", "sort_column", "sort_ascending"},
            {"default_metrics"},
        ),
        (
            Widget.Kind.STACKED_BAR,
            {
                "dimension",
                "sort_column",
                "sort_ascending",
                "second_dimension",
                "stack_100_percent",
            },
            {"optional_metrics"},
        ),
        (
            Widget.Kind.LINE,
            {"dimension", "sort_column", "sort_ascending"},
            {"default_metrics"},
        ),
        (
            Widget.Kind.STACKED_LINE,
            {
                "dimension",
                "sort_column",
                "sort_ascending",
                "second_dimension",
                "stack_100_percent",
            },
            {"optional_metrics"},
        ),
        (
            Widget.Kind.PIE,
            {"dimension", "sort_column", "sort_ascending"},
            {"optional_metrics"},
        ),
        (
            Widget.Kind.AREA,
            {"dimension", "sort_column", "sort_ascending"},
            {"default_metrics"},
        ),
        (
            Widget.Kind.DONUT,
            {"dimension", "sort_column", "sort_ascending"},
            {"default_metrics"},
        ),
        (Widget.Kind.SCATTER, {"dimension", "sort_column", "sort_ascending"}, {"xy"}),
        (Widget.Kind.FUNNEL, {"dimension", "sort_column", "sort_ascending"}, {"min2"}),
        (Widget.Kind.RADAR, {"dimension", "sort_column", "sort_ascending"}, {"min3"}),
        (Widget.Kind.BUBBLE, {"dimension", "sort_column", "sort_ascending"}, {"xyz"}),
        (Widget.Kind.HEATMAP, {"dimension", "second_dimension"}, {"default_metrics"}),
        (Widget.Kind.COMBO, set(), {"combination_chart"}),
    ],
)
def test_widget_generic_form(setup, widget_factory, pwf, kind, fields, formsets):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = GenericWidgetForm(instance=widget, schema=TABLE.schema())

    pwf.render(form)

    pwf.assert_fields({"kind", "date_column"} | fields)
    pwf.assert_formsets({"filters"} | formsets)

    # TODO: metric
    # {"compare_previous_period", "positive_decrease"}

    # if "dimension" in fields:
    #     pwf.assert_select_options_length("dimension", NUM_COLUMN_OPTIONS)

    # if "second_dimension" in fields:
    #     pwf.assert_select_options_length("second_dimension", NUM_COLUMN_OPTIONS)

    # if "sort_column" in fields:
    #     pwf.assert_select_options_length("sort_column", NUM_COLUMN_OPTIONS)
