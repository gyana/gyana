import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.django_db(transaction=True)


def test_dashboards(page, live_server, project, integration_table_factory):
    # uploaded into bigquery as part of test_uploads
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

    # create a table widget and view in the dashboard
    page.locator("#widget-table").drag_to(
        page.locator(".widgets"), target_position={"x": 100, "y": 100}
    )
    page.locator('[data-cy="widget-configure-1"]').click()
    page.get_by_text("store_info").click()
    expect(page.get_by_text("Edinburgh")).to_have_count(3)

    page.locator("button[class*=modal__close]").click()
    expect(page.locator("#widget-1").get_by_text("London")).to_have_count(5)

    # chart with aggregations
    page.locator("#widget-msbar2d").drag_to(
        page.locator(".widgets"), target_position={"x": 100, "y": 600}
    )
    page.locator('[data-cy="widget-configure-2"]').click()
    page.get_by_text("store_info").click()
    page.get_by_text("Continue").click()

    page.locator("select[name=dimension]").select_option("Owner")
    page.locator('[data-pw="formset-default_metrics-add"]').click()
    page.locator("select[name=default_metrics-0-column]").select_option("Employees")
    page.locator("select[name=default_metrics-0-function]").select_option("Sum")
    page.get_by_text("Save & Close").click()
    page.locator("#widget-2").get_by_text("David").wait_for()

    # delete a widget
    # explicit hover on locator does not work
    page.mouse.move(200, 200)
    page.locator("#widget-1 #widget-card__more-button").click()
    # .last is due to react-html-parser and template issue
    page.locator("#widget-1").get_by_text("Delete").last.click()
    expect(page.locator("#widget-1")).not_to_be_attached()

    # share
    page.locator("#dashboard-share-1").click()
    page.locator("select[name=shared_status]").select_option("public")
    page.locator("#dashboard-share-update").click()

    regex = r"http:\/\/localhost:8000\/dashboards\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
    locator = page.get_by_text(re.compile(regex)).first
    locator.wait_for()

    shared_url = locator.text_content()

    page.goto(live_server.url + "/logout")

    page.goto(shared_url.replace("http://localhost:8000", live_server.url))
    page.get_by_text("David").wait_for()
