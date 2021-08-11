from datetime import datetime
from itertools import chain

from apps.base.clients import bigquery_client
from apps.connectors.config import get_services
from apps.connectors.fivetran import FivetranClient
from apps.connectors.models import Connector
from apps.tables.models import Table
from django.db import transaction


def get_tables_in_dataset(connector: Connector):

    client = bigquery_client()

    service_conf = get_services()[connector.service]

    if service_conf["requires_schema_prefix"] == "t":
        bq_tables = chain(
            *[
                client.list_tables(f"{connector.schema}_{schema}")
                for schema in FivetranClient().get_schema(connector.fivetran_id)
            ]
        )
    else:
        bq_tables = list(client.list_tables(connector.schema))

    with transaction.atomic():

        for bq_table in bq_tables:
            # Ignore fivetran managed tables
            if bq_table.table_id == "fivetran_audit":
                continue

            table = Table(
                source=Table.Source.INTEGRATION,
                _bq_table=bq_table.table_id,
                bq_dataset=connector.schema,
                project=connector.integration.project,
                integration=connector.integration,
            )
            table.save()
