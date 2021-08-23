import re

BIGQUERY_TYPE_TO_HUMAN = {
    "ARRAY": None,
    "BOOL": "True/False",
    "BYTES": "Binary",
    "DATE": "Date",
    "DATETIME": "Date & Time",
    "GEOGRAPHY": "Geography",
    "Interval": "Range",
    "INT64": "Number",
    "INT": "Number",
    "SMALLINT": "Number",
    "INTEGER": "Number",
    "BIGINT": "Number",
    "TINYINT": "Number",
    "BYTEINT": "Number",
    "NUMERIC": "Number",
    "DECIMAL": "Number",
    "BIGNUMERIC": "Number",
    "BIGDECIMAL": "Number",
    "FLOAT": "Number",  # undocumented
    "FLOAT64": "Number",
    "STRING": "Text",
    "STRUCT": None,
    "TIME": "Time",
    # technically without timezone
    "TIMESTAMP": "Date & Time",
}

# https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
def get_humanize_from_bigquery_type(type: str):
    # remove paramterised and template type information
    raw_type = type.split("<")[0].split("(")[0]

    # for template types, share raw info for end user
    return BIGQUERY_TYPE_TO_HUMAN.get(raw_type) or type


def sanitize_bigquery_column_name(name: str):
    # https://stackoverflow.com/a/3305731/15425660
    # https://cloud.google.com/bigquery/docs/schemas#column_names
    # replace anything illegal with an underscore, and prefix with underscore if necessary
    # based on experiments this is consistent with the bigquery algorithm
    return re.sub("\W|^(?=\d)", "_", name)[:300]
