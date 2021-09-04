from itertools import chain

import analytics
from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.base.clients import fivetran_client
from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.connectors.config import get_services
from apps.connectors.models import Connector
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table

from .bigquery import get_bq_tables_from_connector


def _get_schema_bq_ids_from_connector(connector: Connector):

    schema_bq_ids = set(
        chain(*(s.enabled_bq_ids for s in fivetran_client().get_schemas(connector)))
    )

    # fivetran schema config does not include schema prefix for databases
    if get_services()[connector.service]["requires_schema_prefix"] == "t":
        schema_bq_ids = {f"{connector.schema}_{id_}" for id_ in schema_bq_ids}

    return schema_bq_ids


def complete_connector_sync(connector: Connector, send_mail: bool = True):
    bq_tables = get_bq_tables_from_connector(connector)
    integration = connector.integration

    schema_bq_ids = _get_schema_bq_ids_from_connector(connector)

    with transaction.atomic():
        for bq_table in bq_tables:
            # filter to the tables user has explicitly chosen, in case bigquery
            # tables failed to delete
            if (
                f"{bq_table.dataset_id}.{bq_table.table_id}" in schema_bq_ids
                # google sheets
                or len(schema_bq_ids) == 0
            ):

                # only replace tables that already exist
                # there is a unique constraint on table_id/dataset_id to avoid duplication
                # todo: turn into a batch update for performance

                table, _ = Table.objects.get_or_create(
                    source=Table.Source.INTEGRATION,
                    bq_table=bq_table.table_id,
                    bq_dataset=bq_table.dataset_id,
                    project=connector.integration.project,
                    integration=connector.integration,
                )
                table.num_rows = table.bq_obj.num_rows
                table.save()

        integration.state = Integration.State.DONE
        integration.save()

    if (created_by := integration.created_by) and send_mail:

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


@shared_task(bind=True)
def poll_fivetran_sync(self, connector_id):

    connector = get_object_or_404(Connector, pk=connector_id)

    fivetran_client().block_until_synced(connector)

    # we've waited for a while, we don't to duplicate this logic
    connector.refresh_from_db()
    complete_connector_sync(connector)


def run_initial_connector_sync(connector: Connector):

    fivetran_client().start_initial_sync(connector)

    return poll_fivetran_sync.delay(connector.id)


def run_update_connector_sync(connector: Connector):

    tables = connector.integration.table_set.all()

    # if we've deleted tables, we'll need to delete them from BigQuery

    schema_bq_ids = _get_schema_bq_ids_from_connector(connector)

    with transaction.atomic():
        for table in tables:
            if table.bq_id not in schema_bq_ids:
                table.delete()

    # re-calculate total rows after tables are deleted
    connector.integration.project.team.update_row_count()

    # if we've added new tables, we need to trigger resync
    # otherwise, we don't want to make the user wait

    bq_ids = {t.bq_id for t in tables}

    if any(s for s in schema_bq_ids if s not in bq_ids):

        fivetran_client().start_update_sync(connector)
        return poll_fivetran_sync.delay(connector.id)

    return None


def run_connector_sync(connector: Connector):

    result = (
        run_initial_connector_sync
        if connector.integration.table_set.count() == 0
        else run_update_connector_sync
    )(connector)

    if result is not None:
        connector.sync_task_id = result.task_id
        connector.sync_started = timezone.now()
        connector.save()

        connector.integration.state = Integration.State.LOAD
        connector.integration.save()
