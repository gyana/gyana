import pytest

from apps.base.tests.asserts import assertOK
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import (
    mock_bq_client_with_records,
    mock_bq_client_with_schema,
)
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db

AUTOCOMPLETE_URL = (
    "/filters/autocomplete?q={q}&column=athlete&parentType=node&parentId={p}"
)

SOURCE_DATA = list(range(5))

FILTER_SQL = "SELECT DISTINCT `athlete`\nFROM `project.dataset.table`\nWHERE STARTS_WITH(lower(`athlete`), {})\nLIMIT 20"


def test_filter_autocomplete(
    client, project, node_factory, integration_table_factory, bigquery
):
    mock_bq_client_with_schema(
        bigquery, [(name, str(type_)) for name, type_ in TABLE.schema().items()]
    )
    mock_bq_client_with_records(bigquery, [{"athlete": x} for x in SOURCE_DATA])

    table = integration_table_factory(project=project)
    input_node = node_factory(
        kind=Node.Kind.INPUT, workflow__project=project, input_table=table
    )
    filter_node = node_factory(kind=Node.Kind.FILTER, workflow__project=project)
    filter_node.parents.add(input_node)

    r = client.get(AUTOCOMPLETE_URL.format(q="", p=filter_node.id))
    assertOK(r)
    assert r.data == SOURCE_DATA
    assert bigquery.get_query_results.call_args[0][0] == FILTER_SQL.format("''")

    r = client.get(AUTOCOMPLETE_URL.format(q="3", p=filter_node.id))
    assertOK(r)
    assert bigquery.get_query_results.call_args[0][0] == FILTER_SQL.format("'3'")
