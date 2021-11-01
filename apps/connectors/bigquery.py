from itertools import chain

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from apps.base import clients
from apps.connectors.fivetran.schema import get_bq_datasets_from_schemas

from .fivetran.config import get_services


def delete_connector_datasets(connector):
    datasets = get_bq_datasets_from_schemas(connector)

    for dataset in datasets:
        clients.bigquery().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )


def get_bq_tables_from_dataset_safe(dataset_id):

    client = clients.bigquery()

    try:
        bq_tables = client.list_tables(dataset_id)
        return [t for t in bq_tables if t.table_id != "fivetran_audit"]

    except NotFound:
        return []


def get_bq_tables_from_connector(connector):

    service_conf = get_services()[connector.service]

    datasets = (
        (
            f"{connector.schema}_{schema.name_in_destination}"
            for schema in clients.fivetran().get_schemas(connector)
        )
        if service_conf.get("requires_schema_prefix") == "t"
        else [connector.schema]
    )

    return list(chain(get_bq_tables_from_dataset_safe(d) for d in datasets))
