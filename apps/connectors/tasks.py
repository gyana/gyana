from datetime import datetime
from itertools import chain
from typing import Optional

import analytics
from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.base.clients import fivetran_client
from apps.base.tasks import honeybadger_check_in
from apps.connectors.fivetran import FivetranClientError
from apps.connectors.models import Connector
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table

from .bigquery import get_bq_tables_from_schemas
from .fivetran_schema import get_bq_ids_from_schemas


def complete_connector_sync(connector: Connector, send_mail: bool = True):
    bq_tables = get_bq_tables_from_schemas(connector)
    integration = connector.integration

    with transaction.atomic():
        for bq_table in bq_tables:
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

    if integration.created_by and send_mail:

        email = integration_ready_email(integration, integration.created_by)
        email.send()

        analytics.track(
            integration.created_by.id,
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

    schema_bq_ids = get_bq_ids_from_schemas(connector)

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


def update_fivetran_succeeded_at(connector: Connector, succeeded_at: Optional[str]):
    if succeeded_at is not None:
        # timezone (UTC) information is parsed automatically
        succeeded_at = datetime.strptime(succeeded_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        if (
            connector.fivetran_succeeded_at is None
            or succeeded_at > connector.fivetran_succeeded_at
        ):
            connector.fivetran_succeeded_at = succeeded_at
            connector.save()

            # update all tables too
            tables = connector.integration.table_set.all()
            for table in tables:
                table.data_updated = succeeded_at
                table.num_rows = table.bq_obj.num_rows

            Table.objects.bulk_update(tables, ["data_updated", "num_rows"])


FIVETRAN_SYNC_FREQUENCY_HOURS = 6


@shared_task
def update_connectors_from_fivetran():

    succeeded_at_before = timezone.now() - timezone.timedelta(
        hours=FIVETRAN_SYNC_FREQUENCY_HOURS
    )

    # checks fivetran connectors every FIVETRAN_SYNC_FREQUENCY_HOURS seconds for
    # possible updated data, until sync has completed
    connectors_to_check = (
        Connector.objects
        # need to include where fivetran_succeeded_at is null
        .exclude(fivetran_succeeded_at__gt=succeeded_at_before).all()
    )

    for connector in connectors_to_check:
        try:
            data = fivetran_client().get(connector)
            update_fivetran_succeeded_at(connector, data["succeeded_at"])
        except FivetranClientError:
            pass

    honeybadger_check_in("ZbIlqq")
