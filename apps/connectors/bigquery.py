from google.api_core.exceptions import NotFound

from apps.base import clients

FIVETRAN_SYSTEM_TABLES = {"fivetran_audit", "fivetran_audit_warning"}


def delete_connector_datasets(connector):
    schema_obj = clients.fivetran().get_schemas(connector)

    for dataset in schema_obj.get_bq_datasets():
        clients.bigquery().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )


def get_bq_ids_from_dataset_safe(dataset_id):

    client = clients.bigquery()

    try:
        bq_tables = client.list_tables(dataset_id)
        return {
            f"{t.dataset_id}.{t.table_id}"
            for t in bq_tables
            if t.table_id not in FIVETRAN_SYSTEM_TABLES
        }

    except NotFound:
        return {}


def check_bq_id_exists(bq_id):

    client = clients.bigquery()

    try:
        client.get_table(bq_id)
        return True

    except NotFound:
        return False
