from django.core.cache import cache
from ibis.expr.types import TableExpr

from apps.base.cache import get_cache_key
from apps.base.clients import bigquery_client, ibis_client

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
    return get_cache_key(id=table.id, data_updated=str(table.data_updated))


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

        # the client is not pickle-able
        tbl.op().source = None
        cache.set(key, tbl, 24 * 3600)

    tbl.op().source = conn

    if (
        table.integration is not None
        and table.integration.kind == table.integration.Kind.CONNECTOR
    ):
        # Drop the intersection of fivetran cols and schema cols
        tbl = tbl.drop(set(tbl.schema().names) & FIVETRAN_COLUMNS)

    return tbl


def get_bq_table_schema_from_table(table: Table):
    client = bigquery_client()
    schema = client.get_table(table.bq_id).schema
    return [t for t in schema if t.name not in FIVETRAN_COLUMNS]
