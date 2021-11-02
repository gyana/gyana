from google.api_core.exceptions import NotFound

from apps.base import clients
from apps.connectors.fivetran.schema import get_bq_datasets_from_schemas

FIVETRAN_SYSTEM_TABLES = {"fivetran_audit", "fivetran_audit_warning"}


def delete_connector_datasets(connector):
    datasets = get_bq_datasets_from_schemas(connector)

    for dataset in datasets:
        clients.bigquery().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )


def get_bq_ids_from_dataset_safe(dataset_id):

    client = clients.bigquery()

    try:
        bq_tables = client.list_tables(dataset_id)
        return [
            f"{t.dataset_id}.{t.table_id}"
            for t in bq_tables
            if t.table_id not in FIVETRAN_SYSTEM_TABLES
        ]

    except NotFound:
        return []


def check_bq_id_exists(bq_id):

    client = clients.bigquery()

    try:
        client.get_table(bq_id)
        return True

    except NotFound:
        return False
