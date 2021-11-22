import pytest

from apps.base.tests.asserts import assertOK
from apps.nodes.models import Node
from apps.workflows.models import Workflow

pytestmark = pytest.mark.django_db


API_URL = "/nodes/api/nodes/"


@pytest.fixture
def setup(workflow_factory, node_factory, project):
    workflows = workflow_factory.create_batch(2, project=project)

    nodes = {}
    for workflow in workflows:
        workflow_nodes = {
            "inputs": node_factory.create_batch(
                2, workflow=workflow, kind=Node.Kind.INPUT
            )
        }
        workflow_nodes["join"] = node_factory(workflow=workflow, kind=Node.Kind.JOIN)
        workflow_nodes["output"] = node_factory(
            workflow=workflow, kind=Node.Kind.OUTPUT
        )
        nodes[workflow] = workflow_nodes

    second_join = nodes[workflows[1]]["join"]
    second_join.parents.add(nodes[workflows[1]]["inputs"][0])
    second_join.parents.add(
        nodes[workflows[1]]["inputs"][1], through_defaults={"position": 1}
    )
    return workflows, nodes


def test_create(client, workflow_factory, project):
    workflow = workflow_factory(project=project)
    r = client.post(
        API_URL, data={"workflow": workflow.id, "kind": Node.Kind.INPUT, "x": 0, "y": 0}
    )
    assert r.status_code == 201

    assert Node.objects.first() is not None


def test_list(client, setup):
    workflows, _ = setup
    r = client.get(API_URL)
    assertOK(r)
    assert r.data["count"] == 8

    # filter by workflow
    r = client.get(f"{API_URL}?workflow={workflows[0].id}")
    assertOK(r)
    assert r.data["count"] == 4


def test_delete(client, setup):
    workflows, nodes = setup
    join_node = nodes[workflows[0]]["join"]
    r = client.delete(f"{API_URL}{join_node.id}/")
    assert r.status_code == 204

    assert (
        Node.objects.filter(workflow=workflows[0], kind=Node.Kind.JOIN).first() is None
    )


def test_get(client, setup):
    workflows, nodes = setup
    input_nodes = nodes[workflows[1]]["inputs"]
    join_node = nodes[workflows[1]]["join"]
    r = client.get(f"{API_URL}{join_node.id}/")
    assertOK(r)
    assert r.json() == {
        "id": join_node.id,
        "kind": "join",
        "name": None,
        "x": 0.0,
        "y": 0.0,
        "workflow": workflows[1].id,
        "parents": [
            {"id": p.id, "parent_id": p.parent_id, "position": p.position}
            for p in join_node.parent_set.all()
        ],
        "description": "None=None inner",
        "error": None,
        "text_text": None,
    }


def test_update(client, setup):
    workflows, nodes = setup
    join_node = nodes[workflows[0]]["join"]
    input_nodes = nodes[workflows[0]]["inputs"]
    # update name
    r = client.patch(
        f"{API_URL}{join_node.id}/",
        data={"name": "Join node"},
        content_type="application/json",
    )
    assertOK(r)
    join_node.refresh_from_db()
    assert join_node.name == "Join node"
    assert len(r.data["parents"]) == 0

    # update parents
    r = client.patch(
        f"{API_URL}{join_node.id}/",
        content_type="application/json",
        data={
            "parents": [
                {
                    "parent_id": input_nodes[0].id,
                }
            ]
        },
    )
    assertOK(r)
    assert join_node.parents.first() == input_nodes[0]

    r = client.patch(
        f"{API_URL}{join_node.id}/",
        content_type="application/json",
        data={
            "parents": [
                {
                    "parent_id": input_nodes[0].id,
                },
                {"parent_id": input_nodes[1].id},
            ]
        },
    )
    assertOK(r)
    assert join_node.parents.count() == 2
    assert join_node.parent_set.filter(parent=input_nodes[1]).first().position == 1

    # not adding a node to the parents removes it
    r = client.patch(
        f"{API_URL}{join_node.id}/",
        content_type="application/json",
        data={
            "parents": [
                {
                    "parent_id": input_nodes[0].id,
                }
            ]
        },
    )
    assertOK(r)
    assert join_node.parents.count() == 1


def test_duplicate(client, setup):
    workflows, nodes = setup
    join_node = nodes[workflows[1]]["join"]
    input_1, input_2 = nodes[workflows[1]]["inputs"]
    r = client.post(f"/nodes/{join_node.id}/duplicate")
    assertOK(r)
    assert Node.objects.filter(workflow=workflows[1], kind=Node.Kind.JOIN).count() == 2
    data = r.json()
    assert data["name"] == "Copy of Join" and data["x"] == 50 and data["y"] == 50
    new_join = Node.objects.filter(workflow=workflows[1], kind=Node.Kind.JOIN).last()
    assert new_join.name == "Copy of Join"
    assert [p.id for p in new_join.parents.all()] == [input_1.id, input_2.id]


def test_update_positions(client, setup):
    workflows, nodes = setup
    input_1, input_2 = nodes[workflows[1]]["inputs"]
    r = client.post(
        f"/workflows/{workflows[1].id}/update_positions",
        data=[
            {"id": str(input_1.id), "x": 10, "y": 10},
            {"id": str(input_2.id), "x": 20, "y": 20},
        ],
        content_type="application/json",
    )
    assertOK(r)
    input_1.refresh_from_db()
    input_2.refresh_from_db()
    assert input_1.x == 10 and input_1.y == 10
    assert input_2.x == 20 and input_2.y == 20
