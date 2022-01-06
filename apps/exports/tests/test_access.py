import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


def test_export_node(client, user, node_factory):
    node = node_factory()
    url = f"/exports/new/node/{node.id}"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    node.workflow.project.team = user.teams.first()
    node.workflow.project.save()
    r = client.get(url)
    assertOK(r)


def test_export_integration_table(client, user, integration_table_factory):
    table = integration_table_factory()
    url = f"/exports/new/integration_table/{table.id}"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    table.integration.project.team = user.teams.first()
    table.integration.project.save()
    r = client.get(url)
    assertOK(r)
