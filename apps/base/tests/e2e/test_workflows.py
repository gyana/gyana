import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.django_db(transaction=True)


def test_workflow_editor(
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
    page.goto(live_server.url + "/projects/1/workflows")

    page.get_by_text("Create a new workflow").click()
    page.locator('input[id="name"]').fill("Magical workflow")

    # drop and configure an input node
    page.locator("#dnd-node-input").drag_to(
        page.locator(".react-flow"),
        target_position={"x": 150, "y": 300},
    )

    page.locator('[data-id="1"]').dblclick()
    page.get_by_text("store_info").click()
    page.get_by_text("Employees").wait_for()
    assert page.get_by_text("Blackpool").count() == 4
    page.locator(".modal__close").click()

    # drop, connect and configure select node
    page.locator("#dnd-node-select").drag_to(
        page.locator(".react-flow"), target_position={"x": 300, "y": 100}
    )
    page.locator('[data-id="2"]').wait_for()
    page.locator('[data-id="1"] .react-flow__handle.source').drag_to(
        page.locator('[data-id="2"] .react-flow__handle.target')
    )

    page.locator('[data-id="2"]').dblclick()
    page.get_by_text("Location").click()
    page.get_by_text("Employees").click()
    page.get_by_text("Owner").click()

    expect(page.get_by_text("Save & Close")).not_to_be_disabled()
    page.get_by_text("Save & Close").click()

    # drop, connect and name output node
    page.locator("#dnd-node-output").drag_to(
        page.locator(".react-flow"), target_position={"x": 450, "y": 300}
    )

    page.locator('[data-id="3"]').wait_for()
    page.locator('[data-id="2"] .react-flow__handle.source').drag_to(
        page.locator('[data-id="3"] .react-flow__handle.target')
    )

    page.locator('[data-id="3"]').dblclick()
    page.locator('#node-update-form input[name="name"]').fill("Goblet of fire")
    page.get_by_text("Save & Close").click()

    # run workflow
    page.locator('[data-cy="workflow-run"]').click()
    page.get_by_text("Last successful run").wait_for()
    page.locator(".fa-sitemap").click()

    page.get_by_text("Magical workflow").wait_for()
    page.locator(".fa-check-circle").hover()
    page.get_by_text("Workflow ran successfully and is up to date").wait_for()
