from ibis import schema
from ibis.expr.operations import DatabaseTable
from ibis.expr.operations.relations import Namespace

from apps.base.clients import get_engine

MOCK_SCHEMA = schema(
    [
        ("id", "int32"),
        ("athlete", "string"),
        ("birthday", "date"),
        ("when", "timestamp"),
        ("lunch", "time"),
        ("medals", "int32"),
        ("stars", "double"),
        ("is_nice", "boolean"),
        ("biography", "struct<a:int32>"),
    ]
)
TABLE = DatabaseTable(
    name="table",
    namespace=Namespace(schema="project.dataset"),
    schema=MOCK_SCHEMA,
    source=get_engine().client,
).to_expr()
