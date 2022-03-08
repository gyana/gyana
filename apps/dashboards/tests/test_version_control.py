import pytest

from apps.base.core.aggregations import AggregationFunctions
from apps.columns.models import AggregationColumn
from apps.controls.models import Control, ControlWidget
from apps.dashboards.models import DashboardVersion
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


def test_restore_dashboard_version(
    widget_factory, control_factory, control_widget_factory
):
    bar_chart = widget_factory(
        kind=Widget.Kind.BAR, dimension="country", date_column="date"
    )
    # bar_chart.filters.create(
    #     column="stars", numeric_predicate="greaterthan", float_value=2.3
    # )
    aggregation = bar_chart.aggregations.create(
        column="rating", function=AggregationFunctions.SUM
    )
    control_factory(widget=bar_chart, page=None)

    first_page = bar_chart.page
    dashboard = first_page.dashboard
    control_widget = control_widget_factory(page=first_page, control__page=first_page)

    # TODO: change dashboard dimensions
    version_1 = DashboardVersion(dashboard=dashboard)
    version_1.save()

    second_page = dashboard.pages.create(position=2)
    table_widget = second_page.widgets.create(kind=Widget.Kind.TABLE)
    table_widget.columns.create(column="country")

    first_page.delete()
    assert dashboard.pages.count() == 1
    assert dashboard.widgets.count() == 1
    assert Control.objects.count() == 0
    assert ControlWidget.objects.count() == 0
    assert AggregationColumn.objects.count() == 0

    version_1.restore()
    assert dashboard.widgets.first() == bar_chart
    assert AggregationColumn.objects.first() == aggregation
    assert Control.objects.count() == 2
    assert ControlWidget.objects.first() == control_widget
