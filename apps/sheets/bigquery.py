import re

from google.cloud import bigquery
from google.cloud.bigquery.job.query import QueryJob

from apps.base import clients
from apps.base.core.bigquery import (
    bq_table_schema_is_string_only,
    sanitize_bq_column_name,
)
from apps.base.core.utils import excel_colnum_string
from apps.tables.models import Table

from .models import Sheet
from .sheets import get_cell_range


def _create_external_table(
    sheet: Sheet, table_id: str, **job_kwargs
) -> bigquery.ExternalConfig:
    """
    Constructs a BQ external config.

    For a Google Sheets integration `url` is required and `cell_range` is optional
    """

    # https://cloud.google.com/bigquery/external-data-drive#python

    external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
    external_config.source_uris = [sheet.url]
    if sheet.sheet_name or sheet.cell_range:
        external_config.options.range = get_cell_range(
            sheet.sheet_name, sheet.cell_range
        )
    for k, v in job_kwargs.items():
        if k == "skip_leading_rows":
            setattr(external_config.options, k, v)
        else:
            setattr(external_config, k, v)

    return bigquery.QueryJobConfig(
        table_definitions={
            table_id: external_config,
        }
    )


CONVERSION_ERROR = re.compile(
    "Could not convert value to (.*). Row ([0-9]*); Col ([0-9]*)"
)


def _load_table(sheet: Sheet, table: Table, **job_kwargs):

    client = clients.bigquery()

    external_table_id = f"{table.bq_table}_external"

    query_job = client.query(
        f"CREATE OR REPLACE TABLE {table.bq_id} AS SELECT * FROM {external_table_id}",
        job_config=_create_external_table(sheet, external_table_id, **job_kwargs),
    )

    # capture external table creation errors

    if query_job.exception():
        error_message = query_job.errors[0]["message"]
        if re.search(CONVERSION_ERROR, error_message):
            type_, row, col = re.search(CONVERSION_ERROR, error_message).groups()
            error_message = (
                f"We could not convert cell {excel_colnum_string(int(col)+1)}{int(row)+1} to {type_}."
                f"Try changing the cell value to the appropiate format and retry the sync."
            )
        raise Exception(error_message)


def import_table_from_sheet(table: Table, sheet: Sheet) -> QueryJob:
    """
    Copy Google Sheet to BigQuery table via temporary external table.

    Having data in a bq table rather than an external source makes using it much faster.

    https://cloud.google.com/bigquery/docs/tables-intro
    """

    client = clients.bigquery()

    _load_table(sheet, table, autodetect=True)

    # see apps/uploads/bigquery.py for motivation

    if bq_table_schema_is_string_only(table.bq_obj):

        # create temporary table but skipping the header rows

        temp_table_id = f"{table.bq_table}_temp"

        job_config = _create_external_table(
            sheet, temp_table_id, autodetect=True, skip_leading_rows=1
        )

        # bigquery does not guarantee the order of rows

        header_query = client.query(
            f"select * from (select * from {table.bq_id} except distinct select * from {temp_table_id}) limit 1",
            job_config=job_config,
        )

        header_rows = list(header_query.result())
        if len(header_rows) == 0:
            raise Exception(
                "Error: We weren't able to automatically detect the schema of your sheet."
            )

        header_values = header_rows[0].values()

        # use the header row to provide an explicit schema

        _load_table(
            sheet,
            table,
            skip_leading_rows=1,
            schema=[
                bigquery.SchemaField(sanitize_bq_column_name(field), "STRING")
                for field in header_values
            ],
        )
