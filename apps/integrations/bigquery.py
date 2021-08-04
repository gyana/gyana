import re
from datetime import datetime

from apps.integrations.models import Integration
from apps.tables.models import Table
from apps.utils.clients import DATASET_ID, bigquery_client, ibis_client
from django.conf import settings
from django.db import transaction
from google.cloud import bigquery

DEFAULT_LIMIT = 50


def create_external_config(
    kind: Integration.Kind, url: str, file: str, cell_range=None
) -> bigquery.ExternalConfig:
    """
    Constructs a BQ external config.

    For a Google Sheets integration `url` is required and `cell_range` is optional

    For a CSV integration `file` is required
    """
    if kind == Integration.Kind.GOOGLE_SHEETS:
        # https://cloud.google.com/bigquery/external-data-drive#python
        external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
        external_config.source_uris = [url]
        # Only include cell range when it exists
        if cell_range:
            external_config.options.range = cell_range
    elif kind == Integration.Kind.CSV:
        # See here for more infomation https://googleapis.dev/python/bigquery/1.24.0/generated/google.cloud.bigquery.external_config.CSVOptions.html
        external_config = bigquery.ExternalConfig("CSV")
        external_config.source_uris = [f"gs://{settings.GS_BUCKET_NAME}/{file}"]
        # TODO: this prevents autodetect to work
        # external_config.options.allow_quoted_newlines = True
        # external_config.options.allow_jagged_rows = True

    external_config.autodetect = True

    return external_config


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
    external_table = client.create_table(external_table, exists_ok=True)


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


def sync_table(
    table: Table,
    kind: Integration.Kind = None,
    url: str = None,
    file: str = None,
    cell_range=None,
):
    external_config = create_external_config(
        kind=kind,
        url=url,
        file=file,
        cell_range=cell_range,
    )
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


def get_tables_in_dataset(integration):

    client = bigquery_client()
    bq_tables = list(client.list_tables(integration.schema))

    with transaction.atomic():

        for bq_table in bq_tables:
            # Ignore fivetran managed tables
            if bq_table.table_id == "fivetran_audit":
                continue

            table = Table(
                source=Table.Source.INTEGRATION,
                _bq_table=bq_table.table_id,
                bq_dataset=integration.schema,
                project=integration.project,
                integration=integration,
            )
            table.save()

        integration.last_synced = datetime.now()
        integration.save()


def get_sheets_id_from_url(url):
    p = re.compile(r"[-\w]{25,}")
    return res.group(0) if (res := p.search(url)) else ""


def get_query_from_integration(integration):

    conn = ibis_client()
    if integration.kind == Integration.Kind.FIVETRAN:
        return conn.table(integration.table_id, database=integration.schema)
    return conn.table(integration.table_id)
