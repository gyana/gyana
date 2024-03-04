import re

import pytest
from playwright.sync_api import expect

from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db(transaction=True)


def test_dashboards(page, live_server, project, integration_table_factory):
    table = integration_table_factory(
        project=project,
        name="upload_000000001",
        namespace="cypress_team_000001_tables",
        num_rows=15,
        integration__name="store_info",
    )

    page.force_login(live_server)
    page.goto(live_server.url + f"/projects/{project.id}/dashboards/")

    page.locator('[data-cy="dashboard-create"]').click()
    page.locator("#dashboards-name input[id=name]").fill("Magical dashboard")

    page.locator("#widget-table").drag_to(
        page.locator(".widgets"), target_position={"x": 100, "y": 100}
    )

    # todo: remove!
    page.wait_for_timeout(500)

    table = Widget.objects.first().id
    chart = table + 1

    page.locator(f'[data-cy="widget-configure-{table}"]').click()
    page.get_by_text("store_info").click()

    expect(page.get_by_text("Edinburgh")).to_have_count(3)

    page.locator("button[class*=modal__close]").click()

    expect(page.locator(f"#widget-{table}").get_by_text("London")).to_have_count(5)

    # chart with aggregations
    page.locator("#widget-msbar2d").drag_to(
        page.locator(".widgets"), target_position={"x": 100, "y": 600}
    )
    page.locator(f'[data-cy="widget-configure-{chart}"]').click()
    page.get_by_text("store_info").click()
    page.get_by_text("Continue").click()

    page.locator("select[name=dimension]").select_option("Owner")
    page.locator('[data-pw="formset-default_metrics-add"]').click()
    page.locator("select[name=default_metrics-0-column]").select_option("Employees")
    page.locator("select[name=default_metrics-0-function]").select_option("Sum")
    page.get_by_text("Save & Close").click()
    page.locator(f"#widget-{chart}").get_by_text("David").wait_for()

    # delete a widget
    # explicit hover on locator does not work
    page.mouse.move(200, 200)
    page.locator(f"#widget-{table} #widget-card__more-button").click()
    # .last is due to react-html-parser and template issue
    page.locator(f"#widget-{table}").get_by_text("Delete").last.click()
    expect(page.locator(f"#widget-{table}")).not_to_be_attached()

    # share
    page.locator("#dashboard-share").click()
    page.locator("select[name=shared_status]").select_option("public")
    page.locator("#dashboard-share-update").click()

    regex = r"http:\/\/localhost:8000\/dashboards\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
    locator = page.get_by_text(re.compile(regex)).first
    locator.wait_for()

    shared_url = locator.text_content()

    page.goto(live_server.url + "/logout")

    page.goto(shared_url.replace("http://localhost:8000", live_server.url))
    page.get_by_text("David").wait_for()
