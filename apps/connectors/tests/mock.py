from apps.connectors.fivetran.config import get_services_obj
from apps.connectors.fivetran.schema import FivetranSchemaObj
from google.cloud.bigquery.table import Table as BqTable


def get_mock_list_tables(num_tables):
    return [BqTable(f"project.dataset.table_{n}") for n in range(1, num_tables + 1)]


def get_mock_schema(num_tables, service="google_analytics"):
    tables = {
        f"table_{n}": {
            "name_in_destination": f"table_{n}",
            "enabled": True,
            "enabled_patch_settings": {"allowed": True},
        }
        for n in range(1, num_tables + 1)
    }
    schema = {
        "name_in_destination": "dataset",
        "enabled": True,
        "tables": tables,
    }
    schema_obj = FivetranSchemaObj(
        {"schema": schema},
        service_conf=get_services_obj()[service],
        schema_prefix="dataset",
    )
    return schema_obj
