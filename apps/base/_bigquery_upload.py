from typing import TYPE_CHECKING

from google.cloud import bigquery
from google.cloud.bigquery.job.load import LoadJob

from apps.base.core.bigquery import (
    bq_table_schema_is_string_only,
    sanitize_bq_column_name,
)

if TYPE_CHECKING:
    from apps.tables.models import Table
    from apps.uploads.models import Upload


def _create_external_table(upload: "Upload", table_id: str, **job_kwargs):
    # https://cloud.google.com/bigquery/external-data-drive#python
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [upload.gcs_uri]
    external_config.options.field_delimiter = upload.field_delimiter_char
    external_config.options.allow_quoted_newlines = True
    external_config.options.allow_jagged_rows = True

    for k, v in job_kwargs.items():
        if k == "skip_leading_rows":
            setattr(external_config.options, k, v)
        else:
            setattr(external_config, k, v)

    return bigquery.QueryJobConfig(table_definitions={table_id: external_config})


def _load_table(upload: "Upload", table: "Table", client, **job_kwargs):
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        field_delimiter=upload.field_delimiter_char,
        allow_quoted_newlines=True,
        allow_jagged_rows=True,
        **job_kwargs,
    )

    load_job = client.load_table_from_uri(
        upload.gcs_uri, table.bq_id, job_config=job_config
    )

    if load_job.exception():
        raise Exception(load_job.errors[0]["message"])


def import_table_from_upload(table: "Table", upload: "Upload", client) -> LoadJob:
    _load_table(upload, table, client, autodetect=True, skip_leading_rows=1)

    # bigquery does not autodetect the column names if all columns are strings
    # https://cloud.google.com/bigquery/docs/schema-detect#csv_header
    # the recommended approach for cost is to reload into bigquery rather than updating names
    # https://cloud.google.com/bigquery/docs/manually-changing-schemas#option_2_exporting_your_data_and_loading_it_into_a_new_table

    if bq_table_schema_is_string_only(table.bq_obj):
        # create temporary table without skipping the header row, so we can get the header names

        temp_table_id = f"{table.bq_table}_temp"

        job_config = _create_external_table(
            upload, temp_table_id, autodetect=True, skip_leading_rows=0
        )

        # bigquery does not guarantee the order of rows
        header_query = client.query(
            f"select * from (select * from {temp_table_id} except distinct select * from {table.bq_id}) limit 1",
            job_config=job_config,
        )

        header_rows = list(header_query.result())
        if len(header_rows) == 0:
            raise Exception(
                "Error: We weren't able to automatically detect the schema of your upload."
            )

        header_values = header_rows[0].values()

        # use the header row to provide an explicit schema

        _load_table(
            upload,
            table,
            client,
            skip_leading_rows=1,
            schema=[
                bigquery.SchemaField(sanitize_bq_column_name(field), "STRING")
                for field in header_values
            ],
        )

    return
