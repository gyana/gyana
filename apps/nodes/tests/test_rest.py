import pytest

from apps.base.tests.asserts import assertOK
from apps.nodes.models import Node

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
