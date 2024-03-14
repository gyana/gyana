import pytest
from pytest_django.asserts import assertContains

from apps.base.tests.asserts import assertLink, assertOK, assertSelectorLength
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


def test_widget_crudl(
    client,
    dashboard_factory,
    project,
    integration_table_factory,
    mock_bigquery,
):
    table = integration_table_factory(project=project)
    dashboard = dashboard_factory(project=project)
    page = dashboard.pages.create()
    dashboard_url = f"/projects/{project.id}/dashboards/{dashboard.id}"
    # TODO: Not used right now, maybe replace _add_widget.html with create.html
    r = client.get(f"{dashboard_url}/widgets/new")
    assertOK(r)
    assertLink(r, dashboard_url, "Back")

    # create
    r = client.post(
        f"{dashboard_url}/widgets/new",
        data={"x": 50, "y": 100, "kind": Widget.Kind.COLUMN, "page": page.id},
    )
    widget = Widget.objects.first()
    assertOK(r)
    assert widget is not None

    # read
    r = client.get(f"{dashboard_url}/widgets/{widget.id}")
    assertOK(r)
    r = client.get_htmx_partial(
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
        },
    )
    widget.refresh_from_db()
    assertOK(r)
    assert widget.table == table

    r = client.post(
        f"{dashboard_url}/widgets/{widget.id}/update",
        data={
            "kind": Widget.Kind.COLUMN,
            "dimension": "athlete",
            "submit": "Submit & Close",
            "filters-TOTAL_FORMS": 0,
            "filters-INITIAL_FORMS": 0,
            "aggregations-TOTAL_FORMS": 0,
            "aggregations-INITIAL_FORMS": 0,
        },
    )
    widget.refresh_from_db()
    assertOK(r)
    assert widget.dimension == "athlete"

    # delete
    r = client.delete(f"{dashboard_url}/widgets/{widget.id}/delete")
    assert Widget.objects.first() is None


def test_widget_move_page(
    client,
    dashboard_factory,
    project,
):
    dashboard = dashboard_factory(project=project)
    page_1 = dashboard.pages.create()
    page_2 = dashboard.pages.create(position=2)
    widget = page_1.widgets.create(kind=Widget.Kind.TABLE)

    url = f"/projects/{project.id}/dashboards/{dashboard.id}/widgets/{widget.id}/move-page"
    r = client.get(url)
    assertOK(r)
    assertSelectorLength(r, "option", 2)

    r = client.post(url, data={"page": page_2.id})
    assert r.status_code == 303
    assert r.url == f"/projects/{project.id}/dashboards/{dashboard.id}?dashboardPage=2"
    widget.refresh_from_db()

    assert widget.page == page_2
