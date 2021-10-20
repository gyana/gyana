from itertools import chain

from apps.base.clients import bigquery_client, fivetran_client
from apps.connectors.fivetran_schema import get_bq_datasets_from_schemas
from apps.connectors.models import Connector


def get_bq_tables_from_connector(connector: Connector):

    client = bigquery_client()

    if connector.is_database:
        datasets = get_bq_datasets_from_schemas(connector)
        bq_tables = chain(client.list_tables(dataset) for dataset in datasets)
    else:
        bq_tables = client.list_tables(connector.schema)

    return [t for t in bq_tables if t.table_id != "fivetran_audit"]


def delete_connector_datasets(connector):
    datasets = get_bq_datasets_from_schemas(connector)

    for dataset in datasets:
        bigquery_client().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )
