from ibis.expr.datatypes import DataType

IBIS_TYPE_TO_HUMAN = {
    "array": "Array",
    "boolean": "True/False",
    "binary": "Binary",
    "date": "Date",
    "timestamp": "Date & Time",
    # TODO: Explore what really exists ibis supports many more things
    "geospatial:geography": "Geography",
    "Interval": "Range",
    "int64": "Number",
    "int32": "Number",
    "int16": "Number",
    "int8": "Number",
    "decimal": "Number",
    "float32": "Number",
    "float64": "Number",
    "float16": "Number",
    "string": "Text",
    "struct": "Dictionary",
    "time": "Time",
}


# https://ibis-project.org/reference/datatypes
def humanize_from_ibis_type(type_: DataType):
    # remove paramterised and template type information
    raw_type = str(type_).split("<")[0].split("(")[0]

    # for template types, share raw info for end user
    return IBIS_TYPE_TO_HUMAN.get(raw_type) or raw_type
