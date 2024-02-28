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

    # todo: fix auto-preview
    # expect(page.locator("Edinburgh")).to_have_count(4)

    page.locator("button[class*=modal__close]").click()

    # todo: fix show widget on close
    # page.locator("#widget-1").get_by_text("London").wait_for()

    # chart with aggregations
    page.locator("#widget-msbar2d").drag_to(
        page.locator(".widgets"), target_position={"x": 100, "y": 400}
    )
    page.locator('[data-cy="widget-configure"]').click()
    page.get_by_text("store_info").click()
    page.get_by_text("Continue").click()

    page.locator("select[name=dimension]").select_option("Owner")
    page.locator('[data-pw="formset-default_metrics-add"]').click()
    page.locator("select[name=default_metrics-0-column]").select_option("Employees")
    page.locator("select[name=default_metrics-0-function]").select_option("Sum")
    page.get_by_text("Save & Close").click()

    # todo: fix auto-reopening modal behaviour

    # todo: fix auto-preview
    # cy.get(`#widget-${widgetStartId + 1}`).within((el) => {
    #   // TODO: check for visibility
    #   cy.wrap(el).contains('text', 'David')
    # })

    # delete a widget
    # todo: fix element is not visible
    # page.locator("#widget-delete-1").click()
    # expect(page.locator("#widget-1")).not_to_be_attached()

    # share
    page.locator("#dashboard-share-1").click()
    page.locator("select[name=shared_status]").select_option("public")
    page.locator("#dashboard-share-update").click()

    # todo: fix share box disappears
    # cy.contains(
    #   /localhost:8000\/dashboards\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/
    # )
    #   .invoke('text')
    #   .then((text) => {
    #     const sharedUrl = text.trim()
    #     cy.logout()

    #     cy.visit(sharedUrl)
    #     cy.contains('David')
    #   })
