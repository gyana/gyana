from ibis import schema

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
