from apps.base.clients import DATASET_ID, bigquery_client
from apps.tables.models import Table
from django.conf import settings
from google.cloud import bigquery
from google.cloud.bigquery.job.load import LoadJob

from .models import Upload


def create_external_upload_config(file: str) -> bigquery.ExternalConfig:
    """
    Constructs a BQ external config.

    For an UPLOAD integration `file` is required
    """

    # See here for more infomation https://googleapis.dev/python/bigquery/1.24.0/generated/google.cloud.bigquery.external_config.CSVOptions.html
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [f"gs://{settings.GS_BUCKET_NAME}/{file}"]
    # TODO: this prevents autodetect to work
    # external_config.options.allow_quoted_newlines = True
    # external_config.options.allow_jagged_rows = True

    external_config.autodetect = True

    return external_config


def import_table_from_upload(table: Table, upload: Upload) -> LoadJob:

    client = bigquery_client()

    bq_dataset = client.get_dataset(DATASET_ID)
    table_reference = bigquery.Table(bq_dataset.table(table.bq_table))

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        autodetect=True,
        skip_leading_rows=1,
        # TODO: this prevents autodetect to work
        # allow_quoted_newlines = True,
        # external_config.options.allow_jagged_rows = True
    )
    uri = f"gs://{settings.GS_BUCKET_NAME}/{upload.file_gcs_path}"

    # load jobs does not overwrite by default
    client.delete_table(table_reference, not_found_ok=True)

    load_job = client.load_table_from_uri(uri, table_reference, job_config=job_config)

    return load_job
