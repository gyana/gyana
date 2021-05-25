import re
from datetime import datetime

from apps.integrations.models import Integration
from apps.tables.models import Table
from django.conf import settings
from django.db import transaction
from google.cloud import bigquery
from lib.clients import DATASET_ID, bigquery_client, ibis_client

DEFAULT_LIMIT = 10


def create_external_config(integration: Integration):
    if integration.kind == Integration.Kind.GOOGLE_SHEETS:
        # https://cloud.google.com/bigquery/external-data-drive#python
        external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
        external_config.source_uris = [integration.url]
        # Only include cell range when it exists
        if integration.cell_range:
            external_config.options.range = integration.cell_range
    elif integration.kind == Integration.Kind.CSV:
        external_config = bigquery.ExternalConfig("CSV")
        external_config.source_uris = [
            f"gs://{settings.GS_BUCKET_NAME}/{integration.file.name}"
        ]

    external_config.autodetect = True

    return external_config


def create_external_table(integration: Integration) -> str:

    client = bigquery_client()
    external_table_id = f"table_{integration.pk}_external"

    bq_dataset = client.get_dataset(DATASET_ID)

    external_table = bigquery.Table(bq_dataset.table(external_table_id))

    external_config = create_external_config(integration)

    external_table.external_data_configuration = external_config
    external_table = client.create_table(external_table, exists_ok=True)

    return external_table_id


def copy_table_from_external_table(integration: Integration, external_table_id: str):

    client = bigquery_client()

    table_id = f"table_{integration.pk}"

    external_config = create_external_config(integration)
    job_config = bigquery.QueryJobConfig(
        table_definitions={external_table_id: external_config}
    )

    client.query(
        f"CREATE OR REPLACE TABLE {DATASET_ID}.{table_id} AS SELECT * FROM {DATASET_ID}.{external_table_id}",
        job_config=job_config,
    ).result()

    return table_id


def sync_integration(integration: Integration):
    external_table_id = create_external_table(integration)
    table_id = copy_table_from_external_table(integration, external_table_id)

    with transaction.atomic():

        if not integration.table_set.exists():
            table = Table(
                source=Table.Source.INTEGRATION,
                bq_table=table_id,
                bq_dataset=DATASET_ID,
                project=integration.project,
                integration=integration,
            )
            table.save()
        else:
            for table in integration.table_set.all():
                table.data_updated = datetime.now()
                table.save()

        integration.last_synced = datetime.now()
        integration.save()


def query_integration(integration: Integration):

    conn = ibis_client()

    table = conn.table(
        integration.table_set.first().bq_table,
        database=integration.schema
        if integration.kind == Integration.Kind.FIVETRAN
        else DATASET_ID,
    )

    return conn.execute(table.limit(DEFAULT_LIMIT))


def get_tables_in_dataset(integration):

    client = bigquery_client()
    bq_tables = list(client.list_tables(integration.schema))

    with transaction.atomic():

        for bq_table in bq_tables:
            table = Table(
                source=Table.Source.INTEGRATION,
                bq_table=bq_table.table_id,
                bq_dataset=integration.schema,
                project=integration.project,
                integration=integration,
            )
            table.save()


def get_sheets_id_from_url(url):
    p = re.compile(r"[-\w]{25,}")
    return res.group(0) if (res := p.search(url)) else ""
