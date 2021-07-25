from ibis.expr.types import TableExpr

from apps.utils.clients import ibis_client

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


def query_table(name: str, database=None) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
    Implicitly drops all Fivetran columns from the result
    """
    conn = ibis_client()

    tbl = conn.table(name, database=database)

    # Drop the intersection of fivetran cols and schema cols
    return tbl.drop(set(tbl.schema().names) & FIVETRAN_COLUMNS)
