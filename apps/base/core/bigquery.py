import re

from .ibis.client import *  # noqa
from .ibis.compiler import *  # noqa


def sanitize_bq_column_name(name: str):
    # https://stackoverflow.com/a/3305731/15425660
    # https://cloud.google.com/bigquery/docs/schemas#column_names
    # replace anything illegal with an underscore, and prefix with underscore if necessary
    # based on experiments this is consistent with the bigquery algorithm
    return re.sub("\W|^(?=\d)", "_", name)[:300]


def bq_table_schema_is_string_only(bq_table):
    # check if bigquery has inferred that all columns for an import are strings
    # https://cloud.google.com/bigquery/docs/schema-detect#csv_header
    return all(
        col.name == f"string_field_{idx}" and col.field_type == "STRING"
        for idx, col in enumerate(bq_table.schema)
    )
