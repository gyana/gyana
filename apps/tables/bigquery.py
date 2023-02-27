from django.conf import settings
from django.core.cache import cache
from ibis.backends import bigquery
from ibis.expr.types import TableExpr

from apps.base import clients
from apps.base.clients import ibis_client
from apps.base.core.utils import md5_kwargs

from .models import Table

BigQueryTable = bigquery.client.BigQueryTable


def _get_cache_key_for_table(table):
    return f"cache-ibis-table-{md5_kwargs(id=table.id, data_updated=str(table.data_updated))}"


def get_query_from_table(table: Table) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
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

    return tbl


def get_bq_table_schema_from_table(table: Table):
    schema = clients.bigquery().get_table(table.bq_id).schema
    return list(schema)
