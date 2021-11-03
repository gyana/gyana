from unittest.mock import Mock

from apps.connectors.fivetran.config import get_services_obj
from apps.connectors.fivetran.schema import FivetranSchemaObj
from google.api_core.exceptions import NotFound

from ..mock import get_mock_list_tables, get_mock_schema


def test_connector_schema_serde():

    # test: serialization and de-serialization

    num_tables = 2

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
    schema_dict = {"schema": schema}
    schema_obj = FivetranSchemaObj(
        schema_dict,
        service_type=get_services_obj()["google_analytics"].service_type,
        schema_prefix="dataset",
    )

    output_schema_dict = schema_obj.to_dict()

    assert schema_dict == output_schema_dict
