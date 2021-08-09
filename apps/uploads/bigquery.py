from django.conf import settings
from google.cloud import bigquery


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
