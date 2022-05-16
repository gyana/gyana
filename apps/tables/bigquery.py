from django.core.cache import cache
from ibis.expr.types import TableExpr

from apps.base import clients
from apps.base.clients import ibis_client
from apps.base.core.utils import md5_kwargs

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
    return f"cache-ibis-table-{md5_kwargs(id=table.id, data_updated=str(table.data_updated))}"


def _set_source(table, source):
    bq_table = table.op()
    kwargs = dict(zip(bq_table.op.argnames, bq_table.args))
    bq_table = bq_table.__class__(**kwargs, source=source)
    table._arg = bq_table


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
        _set_source(tbl, None)
        cache.set(key, tbl, 24 * 3600)

    _set_source(tbl, conn)

    if (
        table.integration is not None
        and table.integration.kind == table.integration.Kind.CONNECTOR
    ):
        # Drop the intersection of fivetran cols and schema cols
        tbl = tbl.drop(set(tbl.schema().names) & FIVETRAN_COLUMNS)

    return tbl


def get_bq_table_schema_from_table(table: Table):
    schema = clients.bigquery().get_table(table.bq_id).schema
    return [t for t in schema if t.name not in FIVETRAN_COLUMNS]
