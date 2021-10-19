from apps.base.bigquery import bq_table_schema_is_string_only, sanitize_bq_column_name
from apps.tables.models import Table
from google.cloud import bigquery
from google.cloud.bigquery.job.query import QueryJob

from .models import Sheet


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
    if sheet.cell_range:
        external_config.options.range = sheet.cell_range
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


def _load_table(sheet: Sheet, table: Table, **job_kwargs):

    from apps.base.clients import bigquery_client

    client = bigquery_client()

    external_table_id = f"{table.bq_table}_external"

    query_job = client.query(
        f"CREATE OR REPLACE TABLE {table.bq_id} AS SELECT * FROM {external_table_id}",
        job_config=_create_external_table(sheet, external_table_id, **job_kwargs),
    )

    # capture external table creation errors

    if query_job.exception():
        raise Exception(query_job.errors[0]["message"])


def import_table_from_sheet(table: Table, sheet: Sheet) -> QueryJob:
    """
    Copy Google Sheet to BigQuery table via temporary external table.

    Having data in a bq table rather than an external source makes using it much faster.

    https://cloud.google.com/bigquery/docs/tables-intro
    """

    from apps.base.clients import bigquery_client

    client = bigquery_client()

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
