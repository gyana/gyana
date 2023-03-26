from django.core.cache import cache
from ibis.expr.types import TableExpr

from apps.base import clients
from apps.base.clients import get_backend_name, ibis_client
from apps.base.core.utils import md5_kwargs

from .models import Table


def _get_cache_key_for_table(table):
    return f"cache-ibis-table-{md5_kwargs(id=table.id, data_updated=str(table.data_updated))}"


def get_query_from_table(table: Table) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
    """

    conn = ibis_client()

    key = _get_cache_key_for_table(table)

    if get_backend_name() == "postgres":
        tbl = conn.table(
            table.bq_table,
            schema=table.bq_dataset,
        )
    else:
        tbl = conn.table(table.bq_table, database=table.bq_dataset)

    cache.set(key, tbl.schema(), 24 * 3600)

    return tbl


def get_bq_table_schema_from_table(table: Table):
    schema = clients.bigquery().get_table(table.bq_id).schema
    return list(schema)
