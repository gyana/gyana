from django.conf import settings
from google.cloud import bigquery

from apps.base import clients


def copy_write_truncate_bq_table(from_table, to_table):
    job_config = bigquery.CopyJobConfig()
    if settings.DEBUG:
        # write truncate required in development
        job_config.write_disposition = "WRITE_TRUNCATE"
    return clients.bigquery().copy_table(from_table, to_table, job_config=job_config)


def copy_table(from_table, to_table):
    """Copies a bigquery table from `from_table` to `to_table.

    Replaces if the table already exists, mostly important to work locally,
    in prod that shouldn't be necessary.
    """
    client = clients.bigquery()

    return client.query(
        f"CREATE OR REPLACE TABLE {to_table} as (SELECT * FROM {from_table})"
    )
