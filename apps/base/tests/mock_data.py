import ibis.expr.datatypes as dt
from ibis import schema

MOCK_SCHEMA = schema(
    [
        ("id", "int32"),
        ("athlete", "string"),
        ("birthday", "date"),
        ("when", dt.Timestamp(timezone="UTC")),
        ("lunch", "time"),
        ("medals", "int32"),
        ("stars", "double"),
        ("is_nice", "boolean"),
        ("biography", "struct<a:int32>"),
    ]
)
