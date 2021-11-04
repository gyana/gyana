from datetime import datetime

from apps.connectors.fivetran.config import get_services_obj
from apps.connectors.fivetran.schema import FivetranSchemaObj
from django.utils import timezone
from google.cloud.bigquery.table import Table as BqTable


def get_mock_list_tables(num_tables, dataset="dataset"):
    return [BqTable(f"project.{dataset}.table_{n}") for n in range(1, num_tables + 1)]


def get_mock_fivetran_connector(
    service="google_analytics",
    schema="dataset",
    is_historical_sync=False,
    is_broken=False,
    succeeded_at=None,
):

    if succeeded_at is not None:
        succeeded_at = datetime.strftime(succeeded_at, "%Y-%m-%dT%H:%M:%S.%f%z")

    data = {
        "id": "fivetran_id",
        "group_id": "group_id",
        "service": service,
        "service_version": 4,
        "schema": schema,
        "paused": True,
        "pause_after_trial": True,
        "connected_by": "monitoring_assuring",
        "created_at": "2021-01-01T00:00:00.000000Z",
        "succeeded_at": succeeded_at,
        "failed_at": None,
        "sync_frequency": 360,
        "schedule_type": "auto",
        "status": {
            "setup_state": "broken" if is_broken else "connected",
            "sync_state": "scheduled",
            "update_state": "delayed",
            "is_historical_sync": is_historical_sync,
            "tasks": [{"code": "reconnect", "message": "Reconnect"}],
            "warnings": [],
        },
        "config": {},
    }

    return data


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
            "columns": {},
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
            service_type=get_services_obj()[service].service_type,
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
        service_type=get_services_obj()[service].service_type,
        schema_prefix="dataset",
    )
    return schema_obj
