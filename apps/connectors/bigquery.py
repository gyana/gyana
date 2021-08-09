from datetime import datetime

from apps.base.clients import bigquery_client
from apps.tables.models import Table
from django.db import transaction


def get_tables_in_dataset(integration):

    client = bigquery_client()
    bq_tables = list(client.list_tables(integration.connector.schema))

    with transaction.atomic():

        for bq_table in bq_tables:
            # Ignore fivetran managed tables
            if bq_table.table_id == "fivetran_audit":
                continue

            table = Table(
                source=Table.Source.INTEGRATION,
                _bq_table=bq_table.table_id,
                bq_dataset=integration.connector.schema,
                project=integration.project,
                integration=integration,
            )
            table.save()

        integration.connector.last_synced = datetime.now()
        integration.save()
