from datetime import datetime

from apps.base.clients import DATASET_ID, bigquery_client
from apps.tables.models import Table
from django.db import transaction
from google.cloud import bigquery

DEFAULT_LIMIT = 50


def create_external_table(table: Table, external_config: bigquery.ExternalConfig):
    """
    Creates an external table. In short, external tables are bq entities that get their data
    from external datasources (such as google sheets and files in gcs).

    https://cloud.google.com/bigquery/external-data-sources

    https://cloud.google.com/bigquery/docs/tables-intro
    """
    client = bigquery_client()

    bq_dataset = client.get_dataset(DATASET_ID)

    external_table = bigquery.Table(bq_dataset.table(table.bq_external_table_id))

    external_table.external_data_configuration = external_config
    # external table does not overwrite by default
    client.delete_table(external_table, not_found_ok=True)
    external_table = client.create_table(external_table)


def copy_table_from_external_table(
    table: Table,
    external_config: bigquery.ExternalConfig,
):
    """
    Copies data from an external table to a native bq table.

    Having data in a bq table rather than an external source makes using it much faster.

    https://cloud.google.com/bigquery/docs/tables-intro
    """
    client = bigquery_client()

    job_config = bigquery.QueryJobConfig(
        table_definitions={table.bq_external_table_id: external_config}
    )

    query_job = client.query(
        f"CREATE OR REPLACE TABLE {DATASET_ID}.{table.bq_table} AS SELECT * FROM {DATASET_ID}.{table.bq_external_table_id}",
        job_config=job_config,
    )

    return query_job


def import_table_from_external_config(
    table: Table, external_config: bigquery.ExternalConfig
):
    create_external_table(table, external_config=external_config)
    query_job = copy_table_from_external_table(table, external_config=external_config)

    yield query_job

    # this halts the function until the query_job is completed
    query_job.result()

    with transaction.atomic():

        table.num_rows = table.bq_obj.num_rows
        table.data_updated = datetime.now()
        table.save()

    # yielding true to signify the end of the integration sync
    yield True
