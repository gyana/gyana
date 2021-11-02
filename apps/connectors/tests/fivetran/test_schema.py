from apps.connectors.fivetran.config import get_services_obj
from apps.connectors.fivetran.schema import FivetranSchemaObj
from google.cloud.bigquery.table import Table as BqTable

from ..mock import get_mock_list_tables, get_mock_schema


def test_connector_schema_serde():

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
        service_conf=get_services_obj()["google_analytics"],
        schema_prefix="dataset",
    )

    output_schema_dict = schema_obj.to_dict()

    assert schema_dict == output_schema_dict


def test_connector_schema_event_tracking(bigquery):

    # test: event_tracking ignores schema and maps the single bigquery table

    schema_obj = get_mock_schema(0, "segment")
    bigquery.list_tables.return_value = get_mock_list_tables(3)

    assert schema_obj.get_bq_ids() == {
        "dataset.table_1",
        "dataset.table_2",
        "dataset.table_3",
    }

    assert bigquery.list_tables.call_count == 1
    assert bigquery.list_tables.call_args.args == ("dataset",)


def test_connector_schema_webhooks_reports(bigquery):

    # test: webhooks_reports maps a single static table, provided it exists

    schema_obj = get_mock_schema(0, "segment")
    bigquery.list_tables.return_value = get_mock_list_tables(3)

    assert schema_obj.get_bq_ids() == {
        "dataset.table_1",
        "dataset.table_2",
        "dataset.table_3",
    }

    assert bigquery.list_tables.call_count == 1
    assert bigquery.list_tables.call_args.args == ("dataset",)
