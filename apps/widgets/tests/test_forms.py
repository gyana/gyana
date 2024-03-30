import pytest

from apps.widgets.forms import GenericWidgetForm, WidgetSourceForm
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(
    project,
    dashboard_factory,
    integration_table_factory,
):

    return dashboard_factory(project=project), integration_table_factory(
        project=project
    )


def test_widget_source_form(setup, widget_factory):
    dashboard, table = setup
    widget = widget_factory(
        kind=Widget.Kind.TABLE, table=table, page__dashboard=dashboard
    )

    form = WidgetSourceForm(instance=widget)
    assert set(form.fields) == {"table"}


def test_widget_generic_form_basic(setup, widget_factory, pwf, engine):
    dashboard, table = setup
    widget = widget_factory(
        kind=Widget.Kind.STACKED_BAR, table=table, page__dashboard=dashboard
    )
    form = GenericWidgetForm(instance=widget, schema=engine.data.schema())

    pwf.render(form)

    # check select options for dimension, second_dimension, sort_column

    pwf.assert_fields(
        {
            "kind",
            "date_column",
            "dimension",
            "sort_column",
            "sort_ascending",
            "second_dimension",
            "stack_100_percent",
        }
    )

    pwf.assert_formsets({"filters", "optional_metrics"})

    # Number is columns plus unselected option
    NUM_COLUMN_OPTIONS = len(engine.data.schema()) + 1
    pwf.assert_select_options_length("dimension", NUM_COLUMN_OPTIONS)
    pwf.assert_select_options_length("second_dimension", NUM_COLUMN_OPTIONS)
    pwf.assert_select_options_length("sort_column", NUM_COLUMN_OPTIONS)

    # check update in kind

    pwf.select_value("kind", Widget.Kind.METRIC)
    pwf.assert_fields({"kind", "date_column"})
    pwf.assert_formsets({"single_metric", "filters"})

    # check date_column changes

    pwf.select_value("date_column", "birthday")
    pwf.assert_fields(
        {"kind", "date_column", "compare_previous_period", "positive_decrease"}
    )
    pwf.assert_formsets({"single_metric", "filters", "controls"})

    # check dimension date => part

    pwf.select_value("kind", Widget.Kind.COLUMN)
    pwf.assert_fields(
        {"kind", "date_column", "dimension", "sort_column", "sort_ascending"}
    )

    pwf.select_value("dimension", "birthday")
    pwf.assert_fields(
        {"kind", "date_column", "dimension", "sort_column", "sort_ascending", "part"}
    )


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
        (Widget.Kind.HEATMAP, {"dimension", "second_dimension"}, {"optional_metrics"}),
        (Widget.Kind.COMBO, set(), {"combo"}),
    ],
)
def test_widget_generic_form(
    setup, widget_factory, pwf, kind, fields, formsets, engine
):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = GenericWidgetForm(instance=widget, schema=engine.data.schema())

    pwf.render(form)

    pwf.assert_fields({"kind", "date_column"} | fields)
    pwf.assert_formsets({"filters"} | formsets)


@pytest.mark.parametrize(
    "kind, min",
    [
        (Widget.Kind.FUNNEL, 2),
        (Widget.Kind.RADAR, 3),
    ],
)
def test_widget_formset_min(setup, widget_factory, pwf, kind, min, engine):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = GenericWidgetForm(instance=widget, schema=engine.data.schema())

    pwf.render(form)

    locator = pwf.page.locator(f'[data-pw="formset-min{min}-remove"]')
    assert locator.count() == min

    for el in locator.all():
        assert el.evaluate("(element) => element.disabled")

    pwf.page.locator(f'[data-pw="formset-min{min}-add"]').click()

    for el in locator.all():
        assert el.evaluate("(element) => !element.disabled")


@pytest.mark.parametrize(
    "kind, prefix, total",
    [
        (Widget.Kind.METRIC, "single_metric", 1),
        (Widget.Kind.SCATTER, "xy", 2),
        (Widget.Kind.BUBBLE, "xyz", 3),
    ],
)
def test_widget_formset_fixed(setup, widget_factory, pwf, kind, prefix, total, engine):
    dashboard, table = setup
    widget = widget_factory(kind=kind, table=table, page__dashboard=dashboard)
    form = GenericWidgetForm(instance=widget, schema=engine.data.schema())

    pwf.render(form)

    locator = pwf.page.locator(f'[data-pw="formset-{prefix}-remove"]')
    assert locator.count() == total

    for remove in locator.all():
        assert remove.evaluate("(element) => element.disabled")

    locator = pwf.page.locator(f'[data-pw="formset-{prefix}-add"]')
    assert locator.evaluate("(element) => element.disabled")
