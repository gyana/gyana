import ibis

TABLE = ibis.table(
    [
        ("id", "int32"),
        ("athlete", "string"),
        ("birthday", "date"),
        ("updated", "timestamp"),
        ("lunch", "time"),
        ("medals", "int32"),
        ("stars", "double"),
        ("is_nice", "boolean"),
    ],
    name="olympians",
)
