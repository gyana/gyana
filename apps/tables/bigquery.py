from django.core.cache import cache
from ibis.expr.types import TableExpr

from apps.base.cache import get_cache_key
from apps.base.clients import bigquery_client, ibis_client
from apps.nodes.models import Node

from .models import Table

# https://fivetran.com/docs/getting-started/system-columns-and-tables#systemcolumns
FIVETRAN_COLUMNS = set(
    [
        "_fivetran_synced",
        "_fivetran_deleted",
        "_fivetran_index",
        "_fivetran_id",
        "_fivetran_active",
        "_fivetran_start",
        "_fivetran_end",
    ]
)


def _get_cache_key_for_table(table):
    data_updated = table.data_updated
    # Cache logic for nodes in workflows, ibis schema is invalidated if any parent
    #  nodes were updated. This is a simple version, we do need to write proper one
    # as this invalidates within the current form.
    if table.workflow_node is not None and table.workflow_node.kind != Node.Kind.OUTPUT:
        data_updated = table.workflow_node.workflow.data_updated
    return get_cache_key(id=table.id, data_updated=str(data_updated))


def get_query_from_table(table: Table) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
    Implicitly drops all Fivetran columns from the result
    """

    conn = ibis_client()

    key = _get_cache_key_for_table(table)
    tbl = cache.get(key)

    if tbl is None:

        tbl = conn.table(table.bq_table, database=table.bq_dataset)

        if (
            table.integration is not None
            and table.integration.kind == table.integration.Kind.CONNECTOR
        ):
            # Drop the intersection of fivetran cols and schema cols
            tbl = tbl.drop(set(tbl.schema().names) & FIVETRAN_COLUMNS)

        # the client is not pickable
        tbl.op().source = None
        cache.set(key, tbl, 30)

    tbl.op().source = conn

    return tbl


def get_bq_table_schema_from_table(table: Table):
    client = bigquery_client()
    schema = client.get_table(table.bq_id).schema
    return [t for t in schema if t.name not in FIVETRAN_COLUMNS]
