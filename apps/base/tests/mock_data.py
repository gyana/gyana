import ibis

TABLE = ibis.table(
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
    ],
    name="olympians",
)
