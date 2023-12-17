from ibis.expr.types import TableExpr

from apps.base.core.utils import md5_kwargs
from apps.base.engine import get_backend_client

from .models import Table


def get_cache_key_for_table(table):
    return f"cache-ibis-table-{md5_kwargs(id=table.id, data_updated=str(table.data_updated))}"


def get_query_from_table(table: Table) -> TableExpr:
    """
    Queries a bigquery table through Ibis client.
    """
    return get_backend_client().get_table(table)
