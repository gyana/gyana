import ibis
from apps.filters.bigquery import create_filter_query
from apps.tables.models import Table
from django.utils import timezone
from ibis.expr.datatypes import String

from lib.bigquery import query_table
from lib.clients import DATAFLOW_ID, bigquery_client, ibis_client
from lib.formulas import to_ibis
from lib.operations import compile_function
from lib.utils import JOINS, get_aggregate_expr, rename_duplicates


def _format_literal(value, type_):
    """Formats a value to the right SQL type to be used in a string query.

    Wraps a string in quotes and replaces spaces from values with `_`
    """
    if value is None:
        return "null"
    if isinstance(type_, String):
        return f'"{value}" {value.replace(" ", "_")}'
    return str(value)


def create_pivot_query(node, parent, client):
    """Creates the pivot query in BigQuery syntax"""
    column_type = parent[node.pivot_column].type()

    # The new column names consist of the values inside the selected column
    names_query = {
        _format_literal(row.values()[0], column_type)
        for row in client.query(parent[node.pivot_column].compile()).result()
    }
    # `pivot_index` is optional and won't be displayed if not selected
    selection = ", ".join(
        filter(None, (node.pivot_index, node.pivot_column, node.pivot_value))
    )

    return (
        f"SELECT * FROM"
        f"  (SELECT {selection} FROM ({parent.compile()}))"
        f"  PIVOT({node.pivot_aggregation}({node.pivot_value})"
        f"      FOR {node.pivot_column} IN ({' ,'.join(names_query)})"
        f"  )"
    )


def create_unpivot_query(node, parent):
    """Creates the unpivot query in BigQuery syntax"""

    selection_columns = [col.column for col in node.secondary_columns.all()]
    selection = (
        f"{' ,'.join(selection_columns)}, {node.unpivot_column}, {node.unpivot_value}"
        if selection_columns
        else "*"
    )
    return (
        f"SELECT {selection} FROM ({parent.compile()})"
        f" UNPIVOT({node.unpivot_value} FOR {node.unpivot_column} IN ({' ,'.join([col.column for col in node.columns.all()])}))"
    )
