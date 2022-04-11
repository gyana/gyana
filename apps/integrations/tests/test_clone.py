import pytest

from apps.connectors.models import Connector
from apps.integrations.models import Integration
from apps.sheets.models import Sheet
from apps.tables.models import Table
from apps.uploads.models import Upload

pytestmark = pytest.mark.django_db(transaction=True)

COPY_QUERY = "CREATE OR REPLACE TABLE {} as (SELECT * FROM {})"


def test_integration_upload_clone(upload_factory, integration_table_factory, bigquery):
    upload = upload_factory()
    table = integration_table_factory(integration=upload.integration)
    clone = upload.integration.make_clone()

    assert Integration.objects.count() == 2
    assert Upload.objects.count() == 2
    assert Table.objects.count() == 2

    clone_table = clone.table_set.first()
    assert clone_table.bq_table == clone.source_obj.table_id

    assert bigquery.query.call_args.args[0] == COPY_QUERY.format(
        clone_table.bq_id, table.bq_id
    )


def test_integration_sheet_clone(sheet_factory, integration_table_factory, bigquery):
    sheet = sheet_factory()
    table = integration_table_factory(integration=sheet.integration)
    clone = sheet.integration.make_clone()

    assert Integration.objects.count() == 2
    assert Sheet.objects.count() == 2
    assert Table.objects.count() == 2

    clone_table = clone.table_set.first()
    assert clone_table.bq_table == clone.source_obj.table_id
    assert clone_table.bq_dataset == table.bq_dataset
    assert bigquery.query.call_args.args[0] == COPY_QUERY.format(
        clone_table.bq_id, table.bq_id
    )


def test_integration_connector_clone(
    connector_factory,
    integration_table_factory,
    bigquery,
    fivetran,
    mock_update_kwargs_from_fivetran,
):
    connector = connector_factory()
    table = integration_table_factory(
        integration=connector.integration, bq_dataset=connector.schema
    )
    config = {
        "group_id": connector.group_id,
        "service": connector.service,
        "config": connector.config,
        "daily_sync_time": "00:00",
    }
    fivetran.get.return_value = config
    fivetran.new.return_value = {"data": config}
    clone = connector.integration.make_clone()

    assert Integration.objects.count() == 2
    assert Connector.objects.count() == 2
    assert Table.objects.count() == 2
    assert connector.schema != clone.connector.schema
    assert clone.connector.schema.startswith(
        f"team_{connector.integration.project.team.id:06}_{clone.connector.service}_"
    )
    assert fivetran.new.call_count == 1
    assert fivetran.get.call_count == 1

    clone_table = clone.table_set.first()
    assert clone_table.bq_table == table.bq_table
    assert clone_table.bq_dataset == clone.connector.schema
    assert bigquery.query.call_args.args[0] == COPY_QUERY.format(
        clone_table.bq_id, table.bq_id
    )
    assert mock_update_kwargs_from_fivetran.call_count == 1
