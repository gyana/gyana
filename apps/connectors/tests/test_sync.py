from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.connectors.sync import (
    _sync_tables_for_connector,
    end_connector_sync,
    start_connector_sync,
)
from apps.integrations.models import Integration

from .mock import get_mock_list_tables, get_mock_schema

pytestmark = pytest.mark.django_db


def test_sync_tables_for_connector(logged_in_user, connector_factory, bigquery):

    team = logged_in_user.teams.first()
    connector = connector_factory(integration__project__team=team)
    integration = connector.integration

    # create new tables
    bq_ids = {"dataset.table_1", "dataset.table_2"}
    connector.actual_bq_ids = bq_ids
    _sync_tables_for_connector(connector)

    assert integration.table_set.count() == 2
    assert integration.table_set.filter(
        bq_dataset="dataset", bq_table="table_2"
    ).exists()
    assert team.row_count == 20

    # no new tables to create
    _sync_tables_for_connector(connector)

    # create two tables, delete a table, update row counts for all
    bigquery.get_table().num_rows = 20

    bq_ids = {"dataset.table_2", "dataset.table_3", "dataset.table_4"}
    connector.actual_bq_ids = bq_ids

    _sync_tables_for_connector(connector)

    assert integration.table_set.count() == 3
    assert not integration.table_set.filter(bq_table="table_1").exists()
    team.refresh_from_db()
    assert team.row_count == 60


def test_start_connector_sync(logged_in_user, connector_factory, fivetran):

    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first(),
        integration__state=Integration.State.LOAD,
        integration__ready=False,
        is_historical_sync=True,
    )
    integration = connector.integration

    # test: start the initial or update connector sync

    # initial sync
    start_connector_sync(connector, None)
    assert fivetran.start_initial_sync.call_count == 1
    assert fivetran.start_initial_sync.call_args.args == (connector,)
    assert connector.fivetran_sync_started is not None
    integration.refresh_from_db()
    assert integration.state == Integration.State.LOAD

    # update sync
    connector.is_historical_sync = False
    connector.save()

    # connector uses schema and not tables updated
    connector.schema_config = get_mock_schema(0).to_dict()
    connector.save()
    start_connector_sync(connector, None)
    assert fivetran.start_update_sync.call_count == 0
    assert connector.integration.state == Integration.State.LOAD

    # connector uses schema and tables updated
    connector.schema_config = get_mock_schema(1).to_dict()
    connector.save()
    start_connector_sync(connector, None)
    assert fivetran.start_update_sync.call_count == 1
    assert fivetran.start_update_sync.call_args.args == (connector,)

    # connector does not use schema
    connector.service = "segment"
    connector.save()
    start_connector_sync(connector, None)
    assert fivetran.start_update_sync.call_count == 2
    assert fivetran.start_update_sync.call_args.args == (connector,)


def test_end_connector_sync(logged_in_user, connector_factory, bigquery):
    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first(),
        integration__state=Integration.State.LOAD,
        integration__ready=False,
        schema_config=get_mock_schema(1).to_dict(),
        fivetran_sync_started=timezone.now(),
        succeeded_at=timezone.now(),
    )
    integration = connector.integration

    # test: logic to handle a completed fivetran sync

    # none of the fivetran tables are available in bigquery yet
    bigquery.list_tables.return_value = get_mock_list_tables(0)

    # api_cloud before grace period
    end_connector_sync(connector, is_initial=True)
    assert integration.state == Integration.State.LOAD

    # api_cloud after grace period
    connector.succeeded_at = timezone.now() - timedelta(hours=1)
    connector.save()
    end_connector_sync(connector, is_initial=True)
    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR

    # event_tracking or webhooks, no grace period
    integration.state = Integration.State.LOAD
    integration.save()
    connector.service = "segment"
    connector.succeeded_at = timezone.now()
    connector.save()
    end_connector_sync(connector, is_initial=True)
    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR

    # data is available in bigquery (with event_tracking)
    integration.state = Integration.State.LOAD
    integration.save()
    # clear the cached property
    del connector.actual_bq_ids
    bigquery.list_tables.return_value = get_mock_list_tables(1)
    end_connector_sync(connector, is_initial=True)
    assert integration.state == Integration.State.DONE
    assert integration.table_set.count() == 1
