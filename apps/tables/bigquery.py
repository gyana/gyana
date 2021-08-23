from apps.base.clients import bigquery_client, ibis_client
from ibis.expr.types import TableExpr

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


def get_query_from_table(table: Table) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
    Implicitly drops all Fivetran columns from the result
    """

    conn = ibis_client()
    tbl = conn.table(table.bq_table, database=table.bq_dataset)

    if (
        table.integration is not None
        and table.integration.kind == table.integration.Kind.CONNECTOR
    ):
        # Drop the intersection of fivetran cols and schema cols
        return tbl.drop(set(tbl.schema().names) & FIVETRAN_COLUMNS)

    return tbl


def get_bq_table_schema_from_table(table: Table):
    client = bigquery_client()
    schema = client.get_table(table.bq_id).schema
    return [t for t in schema if t.name not in FIVETRAN_COLUMNS]
