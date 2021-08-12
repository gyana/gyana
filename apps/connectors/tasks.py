import analytics
from apps.base.clients import fivetran_client
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.connectors.models import Connector
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table
from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .bigquery import get_bq_tables_from_connector


def check_and_complete_connector_sync(connector: Connector):

    is_historical_synced = fivetran_client().is_historical_synced(connector)

    if not is_historical_synced:
        return False

    bq_tables = get_bq_tables_from_connector(connector)
    integration = connector.integration

    with transaction.atomic():

        for bq_table in bq_tables:
            table = Table(
                source=Table.Source.INTEGRATION,
                _bq_table=bq_table.table_id,
                bq_dataset=connector.schema,
                project=connector.integration.project,
                integration=connector.integration,
            )
            table.save()

        integration.state = Integration.State.DONE
        integration.save()

    if created_by := integration.created_by:

        email = integration_ready_email(integration, created_by)
        email.send()

        analytics.track(
            created_by.id,
            INTEGRATION_SYNC_SUCCESS_EVENT,
            {
                "id": integration.id,
                "kind": integration.kind,
                "row_count": integration.num_rows,
                # "time_to_sync": int(
                #     (load_job.ended - load_job.started).total_seconds()
                # ),
            },
        )

    return True


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, connector_id):

    connector = get_object_or_404(Connector, pk=connector_id)

    fivetran_client().block_until_synced(connector)

    # we've waited for a while, we don't to duplicate this logic
    connector.refresh_from_db()
    check_and_complete_connector_sync(connector)


def run_connector_sync(connector: Connector):

    fivetran_client().start(connector)

    result = poll_fivetran_historical_sync.delay(connector.id)
    connector.sync_task_id = result.task_id
    connector.sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()
