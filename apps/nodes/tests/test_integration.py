import pytest
from apps.base.tests.asserts import assertFormRenders, assertOK, assertSelectorText
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(
    bigquery,
    logged_in_user,
    integration_factory,
    integration_table_factory,
    workflow_factory,
):
    team = logged_in_user.teams.first()
    workflow = workflow_factory(project__team=team)
    integration = integration_factory(project=workflow.project, name="olympia")

    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    return (
        integration_table_factory(
            project=workflow.project,
            integration=integration,
        ),
        workflow,
    )


def create_and_connect_node(client, kind, node_factory, table, workflow):
    input_node = node_factory(
        kind=Node.Kind.INPUT, input_table=table, workflow=workflow
    )
    r = client.post(
        "/nodes/api/nodes/",
        data={
            "kind": kind,
            "workflow": workflow.id,
            "x": 50,
            "y": 50,
            "parents": [input_node.id],
        },
    )
    assert r.status_code == 201

    node = Node.objects.get(pk=r.data["id"])
    r = client.get(f"/nodes/{node.id}")
    assertOK(r)

    return node, r


def update_node(client, id, data):
    r = client.post(f"/nodes/{id}", data={"submit": "Save & Preview", **data})
    assert r.status_code == 303
    return r


def test_input_node(client, setup):
    table, workflow = setup
    r = client.post(
        "/nodes/api/nodes/",
        data={"kind": "input", "workflow": workflow.id, "x": 0, "y": 0},
    )
    assert r.status_code == 201
    input_node = Node.objects.first()
    assert input_node is not None

    r = client.get(f"/nodes/{input_node.id}")
    assertSelectorText(r, "label[class=checkbox]", "olympia")
    assertFormRenders(r, ["input_table", "name"])

    r = update_node(client, input_node.id, {"input_table": table.id})
    input_node.refresh_from_db()

    assert r.status_code == 303
    assert input_node.input_table.id == table.id


def test_output_node(client, node_factory, setup):
    table, workflow = setup
    output_node, r = create_and_connect_node(
        client, Node.Kind.OUTPUT, node_factory, table, workflow
    )

    assertFormRenders(r, ["name"])

    r = update_node(client, output_node.id, {"name": "Outrageous"})
    output_node.refresh_from_db()
    assert output_node.name == "Outrageous"
