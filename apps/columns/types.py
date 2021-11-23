from ibis.expr import datatypes as dt

TYPES = {
    "float": dt.float64,
    "int": dt.int64,
    "str": dt.string,
    "time": dt.time,
    "timestamp": dt.timestamp,
    "date": dt.date,
    "text": dt.string,
    "bool": dt.boolean,
}
