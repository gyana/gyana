import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.django_db(transaction=True)


def test_dashboards(
    page, live_server, project, integration_table_factory, celery_worker
):
    table = integration_table_factory(
        project=project,
        name="upload_000000001",
        namespace="cypress_team_000001_tables",
        num_rows=15,
        integration__name="store_info",
    )

    page.force_login(live_server)
    page.goto(live_server.url + f"/projects/1/dashboards/")

    page.locator('[data-cy="dashboard-create"]').click()
    page.locator("#dashboards-name input[id=name]").fill("Magical dashboard")

    page.locator("#widget-table").drag_to(
        page.locator(".widgets"), target_position={"x": 100, "y": 100}
    )
    page.locator('[data-cy="widget-configure"]').click()
    page.get_by_text("store_info").click()

    expect(page.locator("Edinburgh")).to_have_count(4)
