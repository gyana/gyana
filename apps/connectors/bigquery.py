from itertools import chain

from apps.base.clients import bigquery_client, fivetran_client
from apps.connectors.models import Connector


def get_datasets_from_connector(connector):

    datasets = {s.name_in_destination for s in fivetran_client().get_schemas(connector)}

    # fivetran schema config does not include schema prefix for databases
    if connector.is_database:
        datasets = {f"{connector.schema}_{id_}" for id_ in datasets}


def get_bq_tables_from_connector(connector: Connector):

    client = bigquery_client()

    if connector.is_database:
        datasets = get_datasets_from_connector(connector)
        bq_tables = chain(client.list_tables(dataset) for dataset in datasets)
    else:
        bq_tables = client.list_tables(connector.schema)

    return [t for t in bq_tables if t.table_id != "fivetran_audit"]


def delete_connector_datasets(connector):
    datasets = get_datasets_from_connector(connector)

    for dataset in datasets:
        bigquery_client().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )
