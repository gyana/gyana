import pytest

from apps.base.core.aggregations import AggregationFunctions
from apps.columns.models import AggregationColumn
from apps.controls.models import Control, ControlWidget
from apps.dashboards.models import Dashboard, DashboardVersion
from apps.filters.models import Filter
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


def test_restore_dashboard_version(
    widget_factory, control_factory, control_widget_factory
):
    bar_chart = widget_factory(
        kind=Widget.Kind.BAR, dimension="country", date_column="date"
    )
    filter_ = bar_chart.filters.create(
        column="stars", numeric_predicate="greaterthan", float_value=2.3
    )
    aggregation = bar_chart.aggregations.create(
        column="rating", function=AggregationFunctions.SUM
    )
    control_factory(widget=bar_chart, page=None)

    first_page = bar_chart.page
    dashboard = first_page.dashboard
    control_widget = control_widget_factory(page=first_page, control__page=first_page)

    version_1 = DashboardVersion(dashboard=dashboard)
    version_1.save()

    second_page = dashboard.pages.create(position=2)
    table_widget = second_page.widgets.create(kind=Widget.Kind.TABLE)
    table_widget.columns.create(column="country")
    dashboard.width = 500
    dashboard.save()
    first_page.delete()

    version_2 = DashboardVersion(dashboard=dashboard)
    version_2.save()

    assert dashboard.pages.count() == 1
    assert dashboard.widgets.count() == 1
    assert Control.objects.count() == 0
    assert ControlWidget.objects.count() == 0
    assert AggregationColumn.objects.count() == 0

    version_1.dashboard.restore_as_of(version_1.created)
    dashboard.refresh_from_db()
    assert dashboard.width == Dashboard._meta.get_field("width").get_default()
    assert dashboard.widgets.first() == bar_chart
    assert AggregationColumn.objects.first() == aggregation
    assert Control.objects.count() == 2
    assert ControlWidget.objects.first() == control_widget
    assert Filter.objects.first() == filter_

    version_2.dashboard.restore_as_of(version_2.created)
    dashboard.refresh_from_db()
    assert dashboard.width == 500
    assert dashboard.widgets.first() == table_widget
    assert dashboard.pages.first() == second_page
    assert Control.objects.count() == 0
    assert ControlWidget.objects.count() == 0
    assert AggregationColumn.objects.count() == 0
