import pytest

from apps.connectors.fivetran.config import ServiceTypeEnum
from apps.connectors.fivetran.schema import FivetranSchemaObj


@pytest.fixture
def schema_dict():
    yield {
        "schema_1": {"name_in_destination": "schema_1", "enabled": True, "tables": {}},
        "schema_2": {"name_in_destination": "schema_2", "enabled": False, "tables": {}},
        "schema_3": {
            "name_in_destination": "schema_3",
            "enabled": True,
            "tables": {
                "table_1": {
                    "name_in_destination": "table_1",
                    "enabled": False,
                    "enabled_patch_settings": {"allowed": True},
                },
                "table_2": {
                    "name_in_destination": "table_2",
                    "enabled": True,
                    "enabled_patch_settings": {"allowed": True},
                },
                "table_3": {
                    "name_in_destination": "table_3",
                    "enabled": True,
                    "enabled_patch_settings": {"allowed": False},
                },
            },
        },
    }


def test_connector_schema_serde(schema_dict):

    # test: serialization and de-serialization

    schema_obj = FivetranSchemaObj(
        schema_dict,
        service="google_analytics",
        service_type=ServiceTypeEnum.API_CLOUD,
        schema_prefix="dataset",
    )

    output_schema_dict = schema_obj.to_dict()

    assert schema_dict == output_schema_dict


def test_mutate_from_cleaned_data(schema_dict):

    # test: schema is mutated by form data correctly

    schema_obj = FivetranSchemaObj(
        schema_dict,
        service="google_analytics",
        service_type=ServiceTypeEnum.API_CLOUD,
        schema_prefix="dataset",
    )

    cleaned_data = {
        "schema_2_schema": True,
        "schema_3_schema": True,
        "schema_3_tables": ["table_1", "table_3"],
    }

    output_schema_dict = {
        "schema_1": {
            "name_in_destination": "schema_1",
            "enabled": False,
            "tables": {},
        },
        "schema_2": {
            "name_in_destination": "schema_2",
            "enabled": True,
            "tables": {},
        },
        "schema_3": {
            "name_in_destination": "schema_3",
            "enabled": True,
            "tables": {
                "table_1": {
                    "name_in_destination": "table_1",
                    "enabled": True,
                    "enabled_patch_settings": {"allowed": True},
                    "columns": {},
                },
                "table_2": {
                    "name_in_destination": "table_2",
                    "enabled": False,
                    "enabled_patch_settings": {"allowed": True},
                    "columns": {},
                },
            },
        },
    }

    schema_obj.mutate_from_cleaned_data(cleaned_data)

    assert schema_obj.to_dict() == output_schema_dict
