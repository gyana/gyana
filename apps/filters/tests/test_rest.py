import pandas as pd
import pytest
from ibis.backends.bigquery import Backend

from apps.base.tests.asserts import assertOK
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db

AUTOCOMPLETE_URL = (
    "/filters/autocomplete?q={q}&column=athlete&parentType=node&parentId={p}"
)

SOURCE_DATA = list(range(5))

FILTER_SQL = """\
SELECT DISTINCT
  t0.`athlete`
FROM (
  SELECT
    t1.*
  FROM `project.dataset`.table AS t1
  WHERE
    STARTS_WITH(lower(t1.`athlete`), {})
) AS t0
LIMIT 20\
"""


def test_filter_autocomplete(
    client, project, node_factory, integration_table_factory, engine
):
    bq_execute = engine.set_data(pd.DataFrame({"athlete": SOURCE_DATA}))
    table = integration_table_factory(project=project)
    input_node = node_factory(
        kind=Node.Kind.INPUT, workflow__project=project, input_table=table
    )
    filter_node = node_factory(kind=Node.Kind.FILTER, workflow__project=project)
    filter_node.parents.add(input_node)

    r = client.get(AUTOCOMPLETE_URL.format(q="", p=filter_node.id))
    assertOK(r)
    assert r.data == SOURCE_DATA
    assert bq_execute.call_args[0][0].compile() == FILTER_SQL.format("''")

    r = client.get(AUTOCOMPLETE_URL.format(q="3", p=filter_node.id))
    assertOK(r)
    assert bq_execute.call_args[0][0].compile() == FILTER_SQL.format("'3'")
