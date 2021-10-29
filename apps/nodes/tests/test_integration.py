import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertOK,
    assertSelectorLength,
    assertSelectorText,
)
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
    assertSelectorText(r, "label.checkbox", "olympia")
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


def test_select_node(client, node_factory, setup):
    table, workflow = setup

    select_node, r = create_and_connect_node(
        client, Node.Kind.SELECT, node_factory, table, workflow
    )
    assertFormRenders(r, ["name", "select_mode", "select_columns"])
    assertSelectorLength(r, "input[name=select_columns]", 8)
    assertSelectorText(r, "label.checkbox[for=id_select_columns_0]", "id")
    assertSelectorText(r, "label.checkbox[for=id_select_columns_4]", "lunch")

    r = update_node(
        client,
        select_node.id,
        {"select_mode": "exclude", "select_columns": ["birthday", "lunch"]},
    )
    select_node.refresh_from_db()
    assert select_node.select_mode == "exclude"
    assert select_node.columns.count() == 2


def test_join_node(client, node_factory, setup):
    table, workflow = setup

    join_node, r = create_and_connect_node(
        client, Node.Kind.JOIN, node_factory, table, workflow
    )
    assertSelectorText(
        r,
        "p",
        "This node needs to be connected to more than one node before you can configure it.",
    )
    second_input = node_factory(
        kind=Node.Kind.INPUT, input_table=table, workflow=workflow
    )
    join_node.parents.add(second_input)

    r = client.get(f"/nodes/{join_node.id}")
    assertOK(r)
    assertFormRenders(r, ["name", "join_how", "join_left", "join_right"])

    r = update_node(
        client,
        join_node.id,
        {"join_how": "outer", "join_left": "id", "join_right": "id"},
    )
    join_node.refresh_from_db()
    assert join_node.join_how == "outer"
    assert join_node.join_left == "id"
    assert join_node.join_right == "id"


def test_aggregation_node(client, node_factory, setup):
    table, workflow = setup

    aggregation_node, r = create_and_connect_node(
        client, Node.Kind.AGGREGATION, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            "columns-TOTAL_FORMS",
            "aggregations-INITIAL_FORMS",
            "aggregations-TOTAL_FORMS",
            "name",
            "aggregations-__prefix__-node",
            "aggregations-__prefix__-id",
            "aggregations-MIN_NUM_FORMS",
            "aggregations-__prefix__-column",
            "aggregations-__prefix__-DELETE",
            "aggregations-MAX_NUM_FORMS",
            "columns-MAX_NUM_FORMS",
            "columns-MIN_NUM_FORMS",
            "columns-__prefix__-node",
            "columns-__prefix__-column",
            "columns-__prefix__-hidden_live",
            "columns-INITIAL_FORMS",
            "aggregations-__prefix__-hidden_live",
            "columns-__prefix__-DELETE",
            "columns-__prefix__-id",
        ],
    )
