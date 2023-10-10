import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertNotFound, assertOK
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/nodes/{}", id="update"),
        pytest.param("/nodes/{}/grid", id="grid"),
        pytest.param("/nodes/{}/references", id="references"),
        pytest.param("/nodes/{}/name", id="name"),
        pytest.param("/nodes/{}/formula", id="formula"),
        pytest.param("/nodes/{}/function_info?function=abs", id="function_info"),
    ],
)
def test_node_required(client, url, node_factory, user):
    node = node_factory()
    first_url = url.format(node.id)
    assertLoginRedirect(client, first_url)

    client.force_login(user)
    r = client.get(first_url)
    assert r.status_code == 404

    user_node = node_factory(workflow__project__team=user.teams.first())
    r = client.get(url.format(user_node.id))
    assertOK(r)


# Dubplicate only accepts post
def test_duplicate(client, node_factory, user):
    node = node_factory()
    url = f"/nodes/{node.id}/duplicate"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.post(url)
    assert r.status_code == 404

    node.workflow.project.team = user.teams.first()
    node.workflow.project.save()

    r = client.get(url)
    assert r.status_code == 405

    r = client.post(url)
    assertOK(r)


def test_update_positions(client, node_factory, user):
    node = node_factory()
    url = f"/workflows/{node.workflow.id}/update_positions"
    assertLoginRedirect(client, url)

    client.force_login(user)
    data = [
        {"id": str(node.id), "x": 10, "y": 10},
    ]
    r = client.post(
        url,
        data=data,
        content_type="application/json",
    )
    assert r.status_code == 404

    node.workflow.project.team = user.teams.first()
    node.workflow.project.save()

    r = client.post(
        url,
        data=data,
        content_type="application/json",
    )
    assertOK(r)


def test_node_viewset(client, node_factory, user):
    node = node_factory()

    url = f"/nodes/api/nodes/{node.id}/"
    r = client.patch(
        url, data={"kind": Node.Kind.LIMIT}, content_type="application/json"
    )
    assert r.status_code == 403

    client.force_login(user)
    r = client.patch(
        url, data={"kind": Node.Kind.LIMIT}, content_type="application/json"
    )
    assertNotFound(r)

    node.workflow.project.team = user.teams.first()
    node.workflow.project.save()
    r = client.patch(
        url, data={"kind": Node.Kind.LIMIT}, content_type="application/json"
    )
    assertOK(r)


def test_edge_viewset(client, node_factory, user):
    node = node_factory()
    second_node = node_factory()
    second_node.parents.add(node)
    edge = second_node.parent_edges.first()

    url = f"/nodes/api/edges/{edge.id}/"
    r = client.patch(url, data={"position": 0}, content_type="application/json")
    assert r.status_code == 403

    client.force_login(user)
    r = client.patch(url, data={"position": 0}, content_type="application/json")
    assertNotFound(r)

    node.workflow.project.team = user.teams.first()
    node.workflow.project.save()
    r = client.patch(url, data={"position": 0}, content_type="application/json")
    assertOK(r)
