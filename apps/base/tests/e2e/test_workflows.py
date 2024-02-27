import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.django_db(transaction=True)

# // https://github.com/wbkd/react-flow/blob/main/cypress/support/commands.js
# Cypress.Commands.add('reactFlowDrag', (objId, { x, y }) => {
#   return cy
#     .get(`[data-id=${objId}]`)
#     .trigger('mousedown', { which: 1 })
#     .trigger('mousemove', { clientX: x, clientY: y })
#     .trigger('mouseup', { force: true })
# })


def react_flow_drag(page, obj_id, x, y):
    # Select the element
    element = page.query_selector(f'[data-id="{obj_id}"]')

    # Dispatch mousedown event
    page.evaluate(
        f"(element) => {{ element.dispatchEvent(new MouseEvent('mousedown', {{ button: 0 }})); }}",
        element,
    )

    # Dispatch mousemove event
    page.mouse.move(x, y)

    # Dispatch mouseup event
    page.evaluate(
        f"(element) => {{ element.dispatchEvent(new MouseEvent('mouseup', {{ button: 0 }})); }}",
        element,
    )


def connect_nodes(page, source, target):
    # Select the source element
    source_element = page.query_selector(
        f'[data-id="{source}"] .react-flow__handle.source'
    )

    # Dispatch mousedown event on source element
    page.evaluate(
        f"(element) => {{ element.dispatchEvent(new MouseEvent('mousedown', {{ button: 0 }})); }}",
        source_element,
    )

    # Select the target element
    target_element = page.query_selector(
        f'[data-id="{target}"] .react-flow__handle.target'
    )

    # Create a new DataTransfer object
    # data_transfer = page.evaluate("() => new DataTransfer()")

    # Dispatch mousemove event on target element with DataTransfer object
    page.evaluate(
        f"(element, dataTransfer) => {{ element.dispatchEvent(new MouseEvent('mousemove', {{ dataTransfer: new DataTransfer() }})); }}",
        target_element,
        # data_transfer,
    )

    # Dispatch mouseup event on target element with DataTransfer object
    page.evaluate(
        f"(element, dataTransfer) => {{ element.dispatchEvent(new MouseEvent('mouseup', {{ force: true, dataTransfer: new DataTransfer() }})); }}",
        target_element,
        # data_transfer,
    )


def test_workflow_editor(page, live_server, project, integration_table_factory):
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
    page.locator("#dnd-node-input").drag_to(page.locator(".react-flow"))

    page.locator('[data-id="1"]').dblclick()
    page.get_by_text("store_info").click()
    page.get_by_text("Employees").wait_for()
    assert page.get_by_text("Blackpool").count() == 4
    page.locator(".modal__close").click()
    react_flow_drag(page, 1, 150, 300)

    # drop, connect and configure select node
    page.locator("#dnd-node-select").drag_to(page.locator(".react-flow"))
    connect_nodes(page, 1, 2)

    page.pause()
