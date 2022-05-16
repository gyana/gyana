from django.conf import settings
from django.core.cache import cache
from ibis.expr.types import TableExpr
from ibis_bigquery.client import BigQueryTable

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


def get_query_from_table(table: Table) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
    Implicitly drops all Fivetran columns from the result
    """

    conn = ibis_client()

    key = _get_cache_key_for_table(table)
    schema = cache.get(key)

    if schema is None:
        tbl = conn.table(table.bq_table, database=table.bq_dataset)

        cache.set(key, tbl.schema(), 24 * 3600)
    else:
        tbl = TableExpr(
            BigQueryTable(
                name=f"{settings.GCP_PROJECT}.{table.bq_dataset}.{table.bq_table}",
                schema=schema,
                source=conn,
            )
        )

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
