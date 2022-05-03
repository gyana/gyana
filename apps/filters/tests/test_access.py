import pytest

from apps.base.tests.asserts import assertOK
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import (
    mock_bq_client_with_records,
    mock_bq_client_with_schema,
)
from apps.filters.tests.test_rest import SOURCE_DATA
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


def test_access_autocomplete_options(
    client, bigquery, user, node_factory, integration_table_factory
):
    mock_bq_client_with_schema(
        bigquery, [(name, str(type_)) for name, type_ in TABLE.schema().items()]
    )
    mock_bq_client_with_records(bigquery, [{"athlete": x} for x in SOURCE_DATA])

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
