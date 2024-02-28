import pytest
from playwright.sync_api import expect
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db(transaction=True)

BIGQUERY = 30000
SHARED_SHEET = "https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit"


def test_automate(
    page,
    live_server,
    project,
    sheet_factory,
    integration_table_factory,
    workflow_table_factory,
    node_factory,
    workflow_factory,
    celery_worker,
):
    sheet = sheet_factory(
        url=SHARED_SHEET,
        cell_range="",
        integration__project=project,
        integration__name="store_info",
    )
    input_table = integration_table_factory(
        project=project,
        name="sheet_000000001",
        namespace="cypress_team_000001_tables",
        integration=sheet.integration,
    )

    workflow = workflow_factory(project=project)

    input_node = node_factory(
        workflow=workflow, kind=Node.Kind.INPUT, input_table=input_table, name="input"
    )
    output_node = node_factory(workflow=workflow, kind=Node.Kind.OUTPUT, name="output")
    output_node.parents.add(input_node)
    output_node.save()

    workflow_table = workflow_table_factory(
        project=project,
        workflow_node=output_node,
        name="output_node_000000002",
        namespace="cypress_team_000001_tables",
    )

    # todo: add second dependent workflow

    page.force_login(live_server)
    # todo: hack to generate csrf token
    page.goto(live_server.url + "/projects/1/workflows")

    page.get_by_text("Automate").click()

    page.locator('button[data-cy="project-run"]').click()

    expect(page.locator('[data-cy-status="running"]')).to_have_count(1)
    expect(page.locator('[data-cy-status="pending"]')).to_have_count(1)

    expect(page.locator('[data-cy-status="success"]')).to_have_count(
        0, timeout=BIGQUERY + 5
    )

    expect(page.locator('[data-cy-status="success"]')).to_have_count(
        1, timeout=BIGQUERY + 5
    )

    expect(page.locator('[data-cy-status="success"]')).to_have_count(
        2, timeout=BIGQUERY + 5
    )

    page.locator('button[data-cy="settings"]').click()
    expect(page.locator("table tbody tr")).to_have_count(1)
