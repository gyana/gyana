from unittest.mock import Mock

import pytest
from apps.connectors.bigquery import get_bq_tables_for_connector
from google.api_core.exceptions import NotFound
from google.cloud.bigquery.table import Table as BqTable

from .mock import get_mock_list_tables, get_mock_schema

pytestmark = pytest.mark.django_db


def _get_bq_ids(bq_tables):
    return {f"{t.dataset_id}.{t.table_id}" for t in bq_tables}


def test_get_bq_tables_for_connector_event_tracking(
    bigquery, connector_factory, logged_in_user
):
    connector = connector_factory(
        service="segment",
        integration__project__team=logged_in_user.teams.first(),
    )

    # test: event_tracking ignores schema and maps the single bigquery table

    bigquery.list_tables.return_value = get_mock_list_tables(3)

    bq_tables = get_bq_tables_for_connector(connector)

    assert _get_bq_ids(bq_tables) == {
        "dataset.table_1",
        "dataset.table_2",
        "dataset.table_3",
    }

    assert bigquery.list_tables.call_count == 1
    assert bigquery.list_tables.call_args.args == ("dataset",)


def test_get_bq_tables_for_connector_webhooks_reports(
    bigquery, connector_factory, logged_in_user
):

    connector = connector_factory(
        service="webhooks",
        schema="dataset.webhooks_table",
        integration__project__team=logged_in_user.teams.first(),
    )

    # test: webhooks_reports maps a single static table, provided it exists

    def raise_(exc):
        raise exc

    bigquery.get_table = lambda x: raise_(NotFound("not found"))
    bq_tables = get_bq_tables_for_connector(connector)
    assert _get_bq_ids(bq_tables) == set()

    bigquery.get_table = Mock(return_value=BqTable("project.dataset.webhooks_table"))
    bq_tables = get_bq_tables_for_connector(connector)
    assert _get_bq_ids(bq_tables) == {"dataset.webhooks_table"}

    assert bigquery.get_table.call_count == 1
    assert bigquery.get_table.call_args.args == ("dataset.webhooks_table",)


def test_get_bq_tables_for_connector_api_cloud(
    bigquery, connector_factory, logged_in_user
):

    schema_obj = get_mock_schema(3, "google_analytics", disabled=[2])
    connector = connector_factory(
        service="google_analytics",
        schema_config=schema_obj.to_dict(),
        integration__project__team=logged_in_user.teams.first(),
    )

    # test: api_cloud maps the intersection of bigquery and enabled tables in fivetran

    # table_2 is disabled in fivetran and should be ignored
    bigquery.list_tables.return_value = get_mock_list_tables(0)
    bq_tables = get_bq_tables_for_connector(connector)
    assert _get_bq_ids(bq_tables) == set()

    # table_4 in bigquery is not in fivetran schema and should be ignored
    bigquery.list_tables.return_value = get_mock_list_tables(4)
    bigquery.list_tables.reset_mock()

    bq_tables = get_bq_tables_for_connector(connector)
    assert _get_bq_ids(bq_tables) == {"dataset.table_1", "dataset.table_3"}

    assert bigquery.list_tables.call_count == 1
    assert bigquery.list_tables.call_args.args == ("dataset",)


def test_get_bq_tables_for_connector_database(
    bigquery, connector_factory, logged_in_user
):

    # table_2 and schema_2 is disabled in fivetran and should be ignored
    schema_obj = get_mock_schema(
        3, "postgres", disabled=[2], num_schemas=3, schemas_disabled=[2]
    )
    connector = connector_factory(
        service="postgres",
        schema_config=schema_obj.to_dict(),
        integration__project__team=logged_in_user.teams.first(),
    )

    # test: api_cloud maps the intersection of bigquery and enabled tables in fivetran

    # table_4 in bigquery is not in fivetran schema and should be ignored
    bigquery.list_tables.side_effect = lambda dataset_id: get_mock_list_tables(
        4, dataset_id
    )

    bq_tables = get_bq_tables_for_connector(connector)
    assert _get_bq_ids(bq_tables) == {
        "dataset_schema_1.table_1",
        "dataset_schema_1.table_3",
        "dataset_schema_3.table_1",
        "dataset_schema_3.table_3",
    }

    assert bigquery.list_tables.call_count == 2
    assert bigquery.list_tables.call_args_list[0].args == ("dataset_schema_1",)
    assert bigquery.list_tables.call_args_list[1].args == ("dataset_schema_3",)
