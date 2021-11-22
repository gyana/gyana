import pytest
from pytest_django.asserts import assertContains, assertRedirects
from turbo_response.response import TurboStreamResponse

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


def test_widget_crudl(
    client,
    dashboard_factory,
    project,
    integration_table_factory,
    bigquery,
    widget_factory,
):
    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    table = integration_table_factory(project=project)
    dashboard = dashboard_factory(project=project)

    dashboard_url = f"/projects/{project.id}/dashboards/{dashboard.id}"
    # TODO: Not used right now, maybe replace _add_widget.html with create.html
    r = client.get(f"{dashboard_url}/widgets/new")
    assertOK(r)
    assertLink(r, dashboard_url, "Back")

    # create
    r = client.post(
        f"{dashboard_url}/widgets/new",
        data={"kind": Widget.Kind.COLUMN},
    )
    widget = Widget.objects.first()
    assertOK(r)
    assert isinstance(r, TurboStreamResponse)
    assert widget is not None

    # read
    r = client.get(f"{dashboard_url}/widgets/{widget.id}")
    assertOK(r)
    r = client.get_turbo_frame(
        f"{dashboard_url}/widgets/{widget.id}",
        f"{dashboard_url}/widgets/{widget.id}/output",
    )
    assertOK(r)
    assertContains(r, "This widget needs to be")

    # update
    r = client.get(f"{dashboard_url}/widgets/{widget.id}/update")
    assertOK(r)
    # Cant check form fields because table and kind inputs are in webcomponents

    r = client.post(
        f"{dashboard_url}/widgets/{widget.id}/update",
        data={
            "table": table.id,
            "kind": Widget.Kind.COLUMN,
            "dimension": "athlete",
            "sort_by": "dimension",
            "submit": "Submit & Close",
            "filters-TOTAL_FORMS": 0,
            "filters-INITIAL_FORMS": 0,
            "aggregations-TOTAL_FORMS": 0,
            "aggregations-INITIAL_FORMS": 0,
        },
    )
    widget.refresh_from_db()
    assert isinstance(r, TurboStreamResponse)
    assert widget.table == table
    assert widget.dimension == "athlete"

    # delete
    r = client.delete(f"{dashboard_url}/widgets/{widget.id}/delete")
    assert Widget.objects.first() is None

    # list
    widget_factory.create_batch(
        10, kind=Widget.Kind.COLUMN, dashboard=dashboard, table=table
    )
    r = client.get(f"{dashboard_url}/widgets/")
    assertOK(r)
    assertSelectorLength(r, "gy-widget", 10)
