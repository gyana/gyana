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


def complete_connector_sync(connector: Connector, send_mail: bool = True):
    bq_tables = get_bq_tables_from_connector(connector)
    integration = connector.integration

    with transaction.atomic():
        for bq_table in bq_tables:
            # only replace tables that already exist
            # there is a unique constraint on table_id/dataset_id to avoid duplication
            # todo: turn into a batch update for performance
            Table.objects.get_or_create(
                source=Table.Source.INTEGRATION,
                _bq_table=bq_table.table_id,
                bq_dataset=bq_table.dataset_id,
                project=connector.integration.project,
                integration=connector.integration,
            )

        integration.state = Integration.State.DONE
        integration.save()

    if created_by := integration.created_by and send_mail:

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


def resync_connector(connector: Connector) -> bool:

    schemas = fivetran_client().get_schema(connector)

    tables = connector.integration.table_set.all()

    current_bq_ids = {t.bq_id for t in tables}
    new_bq_ids = {
        f"{schema['name_in_destination']}.{table['name_in_destination']}"
        for schema in schemas.values()
        for table in schema["tables"].values()
    }

    delete_tables = [t for t in tables if t.bq_id not in new_bq_ids]
    create_tables = any(s for s in new_bq_ids if s not in current_bq_ids)

    # if we've deleted tables, we'll need to delete them from BigQuery
    with transaction.atomic():
        for table in delete_tables:
            table.delete()

    # if we've added new tables, we need to trigger resync
    # otherwise, we don't want to make the user wait
    if create_tables:
        fivetran_client().resync()

    return create_tables


@shared_task(bind=True)
def poll_fivetran_sync(self, connector_id):

    connector = get_object_or_404(Connector, pk=connector_id)

    fivetran_client().block_until_synced(connector)

    # we've waited for a while, we don't to duplicate this logic
    connector.refresh_from_db()
    complete_connector_sync(connector)


def run_initial_connector_sync(connector: Connector):

    fivetran_client().start(connector)

    return poll_fivetran_sync.delay(connector.id)


def run_update_connector_sync(connector: Connector):

    is_resyncing = fivetran_client().resync(connector)

    if is_resyncing:
        return poll_fivetran_sync.delay(connector.id)


def run_connector_sync(connector: Connector):

    result = (
        run_initial_connector_sync
        if connector.integration.table_set.count() == 0
        else run_update_connector_sync
    )(connector)

    if result:
        connector.sync_task_id = result.task_id
        connector.sync_started = timezone.now()
        connector.save()

        connector.integration.state = Integration.State.LOAD
        connector.integration.save()
