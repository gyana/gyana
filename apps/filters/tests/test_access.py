import pytest

from apps.base.tests.asserts import assertOK
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


def test_access_autocomplete_options(
    client, user, node_factory, integration_table_factory
):
    table = integration_table_factory()
    input_node = node_factory(kind=Node.Kind.INPUT, input_table=table)
    node = node_factory(kind=Node.Kind.FILTER)
    node.parents.add(input_node)
    url = (
        f"/filters/autocomplete?q=us&column=athlete&parentType=node&parentId={node.id}"
    )

    r = client.get(url)
    assert r.status_code == 302

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    node.workflow.project.team = user.teams.first()
    node.workflow.project.save()
    r = client.get(url)
    assertOK(r)
