from unittest.mock import MagicMock

import pytest
from pytest_django.asserts import assertContains

from apps.base.tests.asserts import assertOK
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


@pytest.fixture
def export_to_gcs(mocker):
    return mocker.patch(
        "apps.exports.frames.export_to_gcs",
    )


def test_export_create_node(client, node_factory, export_to_gcs, logged_in_user):

    node = node_factory(kind=Node.Kind.INPUT)
    r = client.get(f"/exports/new/node/{node.id}")
    assertOK(r)
    assertContains(r, "fa-download")

    r = client.post(f"/exports/new/node/{node.id}")

    assert r.status_code == 303
    assert export_to_gcs.delay.call_count == 1
    assert export_to_gcs.delay.call_args.args[1] == logged_in_user.id


def test_export_create_integration_table(
    client, integration_table_factory, export_to_gcs, logged_in_user
):

    table = integration_table_factory()
    r = client.get(f"/exports/new/integration_table/{table.id}")
    assertOK(r)
    assertContains(r, "fa-download")

    r = client.post(f"/exports/new/integration_table/{table.id}")

    assert r.status_code == 303
    assert export_to_gcs.delay.call_count == 1
    assert export_to_gcs.delay.call_args.args[1] == logged_in_user.id
