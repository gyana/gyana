from apps.connectors.fivetran.config import get_services_obj
from apps.connectors.fivetran.schema import FivetranSchemaObj
from google.cloud.bigquery.table import Table as BqTable


def get_mock_list_tables(num_tables, dataset="dataset"):
    return [BqTable(f"project.{dataset}.table_{n}") for n in range(1, num_tables + 1)]


def get_mock_schema(
    num_tables,
    service="google_analytics",
    disabled=None,
    num_schemas=None,
    schemas_disabled=None,
):
    tables = {
        f"table_{n}": {
            "name_in_destination": f"table_{n}",
            "enabled": disabled is None or n not in disabled,
            "enabled_patch_settings": {"allowed": True},
        }
        for n in range(1, num_tables + 1)
    }
    if num_schemas is None:
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

    schemas = [
        {
            "name_in_destination": f"schema_{n}",
            "enabled": schemas_disabled is None or n not in schemas_disabled,
            "tables": tables,
        }
        for n in range(1, num_schemas + 1)
    ]

    schema_obj = FivetranSchemaObj(
        {schema["name_in_destination"]: schema for schema in schemas},
        service_conf=get_services_obj()[service],
        schema_prefix="dataset",
    )
    return schema_obj
