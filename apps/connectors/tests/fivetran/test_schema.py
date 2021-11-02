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

    schema_obj = get_mock_schema(0, "webhooks")

    def raise_(exc):
        raise exc

    bigquery.get_table = lambda x: raise_(NotFound("not found"))
    assert schema_obj.get_bq_ids() == set()

    bigquery.get_table = Mock()

    assert schema_obj.get_bq_ids() == {"dataset.webhooks_table"}

    assert bigquery.get_table.call_count == 1
    assert bigquery.get_table.call_args.args == ("dataset.webhooks_table",)


def test_connector_schema_api_cloud(bigquery):

    # test: api_cloud maps the intersection of bigquery and enabled tables in fivetran

    # table_2 is disabled in fivetran and should be ignored
    schema_obj = get_mock_schema(3, "google_analytics", disabled=[2])
    bigquery.list_tables.return_value = get_mock_list_tables(0)

    assert schema_obj.get_bq_ids() == set()

    # table_4 in bigquery is not in fivetran schema and should be ignored
    bigquery.list_tables.return_value = get_mock_list_tables(4)
    bigquery.list_tables.reset_mock()

    assert schema_obj.get_bq_ids() == {"dataset.table_1", "dataset.table_3"}

    assert bigquery.list_tables.call_count == 1
    assert bigquery.list_tables.call_args.args == ("dataset",)


def test_connector_schema_database(bigquery):

    # test: api_cloud maps the intersection of bigquery and enabled tables in fivetran

    # table_2 and schema_2 is disabled in fivetran and should be ignored
    schema_obj = get_mock_schema(
        3, "postgres", disabled=[2], num_schemas=3, schemas_disabled=[2]
    )
    # table_4 in bigquery is not in fivetran schema and should be ignored
    bigquery.list_tables.side_effect = lambda dataset_id: get_mock_list_tables(
        4, dataset_id
    )

    assert schema_obj.get_bq_ids() == {
        "dataset_schema_1.table_1",
        "dataset_schema_1.table_3",
        "dataset_schema_3.table_1",
        "dataset_schema_3.table_3",
    }

    assert bigquery.list_tables.call_count == 2
    assert bigquery.list_tables.call_args_list[0].args == ("dataset_schema_1",)
    assert bigquery.list_tables.call_args_list[1].args == ("dataset_schema_3",)
