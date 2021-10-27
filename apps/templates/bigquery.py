from apps.base import clients
from django.conf import settings
from google.cloud import bigquery


def copy_write_truncate_bq_table(from_table, to_table):
    job_config = bigquery.CopyJobConfig()
    if settings.DEBUG:
        # write truncate required in development
        job_config.write_disposition = "WRITE_TRUNCATE"
    clients.bigquery().copy_table(from_table, to_table, job_config=job_config)
