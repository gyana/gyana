from apps.base.clients import bigquery_client
from django.conf import settings
from google.cloud import bigquery


def copy_write_truncate_bq_table(from_table, to_table):
    job_config = bigquery.CopyJobConfig()
    if settings.DEBUG:
        # write truncate required in development
        job_config.write_disposition = "WRITE_TRUNCATE"
    bigquery_client().copy_table(from_table, to_table, job_config=job_config)
