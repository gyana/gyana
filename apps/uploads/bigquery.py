from apps.base.clients import bigquery_client
from apps.tables.models import Table
from django.conf import settings
from google.cloud import bigquery
from google.cloud.bigquery.job.load import LoadJob

from .models import Upload


def _is_all_string(bq_table):
    return all(
        col.name == f"string_field_{idx}" and col.field_type == "STRING"
        for idx, col in enumerate(bq_table.schema)
    )


def _load_table(upload, uri, table_reference, **job_kwargs):

    client = bigquery_client()

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        field_delimiter=upload.field_delimiter_char,
        **job_kwargs
        # TODO: this prevents autodetect to work
        # allow_quoted_newlines = True,
        # external_config.options.allow_jagged_rows = True
    )
    uri = f"gs://{settings.GS_BUCKET_NAME}/{upload.file_gcs_path}"

    load_job = client.load_table_from_uri(uri, table_reference, job_config=job_config)

    if load_job.exception():
        raise Exception(load_job.errors[0]["message"])


def import_table_from_upload(table: Table, upload: Upload) -> LoadJob:

    client = bigquery_client()

    bq_dataset = client.get_dataset(table.bq_dataset)
    table_reference = bigquery.Table(bq_dataset.table(table.bq_table))

    uri = f"gs://{settings.GS_BUCKET_NAME}/{upload.file_gcs_path}"

    _load_table(upload, uri, table_reference, autodetect=True, skip_leading_rows=1)

    # bigquery does not autodetect the column names if all columns are strings
    # https://cloud.google.com/bigquery/docs/schema-detect#csv_header
    # the recommended approach for cost is to reload into bigquery rather than updating names
    # https://cloud.google.com/bigquery/docs/manually-changing-schemas#option_2_exporting_your_data_and_loading_it_into_a_new_table

    if _is_all_string(table.bq_obj):

        # reload the table again without skipping the header row, so we can get the header names

        _load_table(upload, uri, table_reference, autodetect=True, skip_leading_rows=0)

        headers = next(
            client.query(f"select * from {table.bq_id} limit 1").result()
        ).values()

        # use the header row to provide an explicit schema

        _load_table(
            upload,
            uri,
            table_reference,
            skip_leading_rows=1,
            schema=[bigquery.SchemaField(field, "STRING") for field in headers],
        )

    return
