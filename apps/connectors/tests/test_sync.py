from datetime import timedelta

import pytest
from apps.connectors.sync import handle_syncing_connector, start_connector_sync
from apps.integrations.models import Integration
from django.utils import timezone

from .mock import get_mock_fivetran_connector, get_mock_list_tables, get_mock_schema

pytestmark = pytest.mark.django_db


def test_start_connector_sync(logged_in_user, connector_factory, fivetran, bigquery):

    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first(),
        integration__state=Integration.State.LOAD,
        integration__ready=False,
    )
    integration = connector.integration

    # test: start the initial or update connector sync

    # initial sync
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector, is_historical_sync=True
    )

    start_connector_sync(connector)
    assert fivetran.start_initial_sync.call_count == 1
    assert fivetran.start_initial_sync.call_args.args == (connector,)
    assert connector.fivetran_sync_started is not None
    integration.refresh_from_db()
    assert integration.state == Integration.State.LOAD

    # update sync
    fivetran.get.return_value = get_mock_fivetran_connector(connector)

    # connector uses schema and not tables updated
    fivetran.get_schemas.return_value = get_mock_schema(0)
    start_connector_sync(connector)
    assert fivetran.start_update_sync.call_count == 0
    assert connector.integration.state == Integration.State.LOAD

    # connector uses schema and tables updated
    fivetran.get_schemas.return_value = get_mock_schema(1)
    start_connector_sync(connector)
    assert fivetran.start_update_sync.call_count == 1
    assert fivetran.start_update_sync.call_args.args == (connector,)

    # connector does not use schema
    connector.service = "segment"
    connector.save()
    start_connector_sync(connector)
    assert fivetran.start_update_sync.call_count == 2
    assert fivetran.start_update_sync.call_args.args == (connector,)


def test_handle_syncing_connector(
    logged_in_user, connector_factory, fivetran, bigquery
):
    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first(),
        integration__state=Integration.State.LOAD,
        integration__ready=False,
        service="google_analytics",
    )
    integration = connector.integration

    # test: logic to handle a syncing fivetran connector, including all errors

    # fivetran setup is broken or incomplete
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector, is_historical_sync=True, is_broken=True
    )
    handle_syncing_connector(connector)
    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR

    # the historical or incremental sync is ongoing
    integration.state = Integration.State.LOAD
    integration.save()
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector, is_historical_sync=True
    )
    handle_syncing_connector(connector)
    integration.refresh_from_db()
    assert integration.state == Integration.State.LOAD

    # none of the fivetran tables are available in bigquery yet
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector,
    )
    fivetran.get_schemas.return_value = get_mock_schema(0)
    bigquery.list_tables.return_value = get_mock_list_tables(0)

    # api_cloud before grace period
    handle_syncing_connector(connector)
    integration.refresh_from_db()
    assert integration.state == Integration.State.LOAD

    # api_cloud after grace period
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector, succeeded_at=timezone.now() - timedelta(hours=1)
    )
    handle_syncing_connector(connector)
    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR

    # event_tracking or webhooks, no grace period
    integration.state = Integration.State.LOAD
    integration.save()
    connector.service = "segment"
    connector.save()
    fivetran.get.return_value = get_mock_fivetran_connector(connector)
    handle_syncing_connector(connector)
    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR

    # data is available in bigquery (with event_tracking)
    integration.state = Integration.State.LOAD
    integration.save()
    fivetran.get_schemas.return_value = get_mock_schema(0, service="segment")
    bigquery.list_tables.return_value = get_mock_list_tables(1)
    bigquery.get_table().num_rows = 10
    handle_syncing_connector(connector)
    assert integration.state == Integration.State.DONE
    assert integration.table_set.count() == 1
