from google.cloud import bigquery
from google.cloud.bigquery.job.load import LoadJob

from apps.base import clients
from apps.tables.models import Table

from .models import CustomApi


def import_table_from_customapi(table: Table, customapi: CustomApi) -> LoadJob:

    client = clients.bigquery()

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )

    load_job = client.load_table_from_uri(
        customapi.gcs_uri, table.bq_id, job_config=job_config
    )

    if load_job.exception():
        raise Exception(load_job.errors[0]["message"])

    return
