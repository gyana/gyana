from typing import List

import analytics
from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.connectors.models import Connector
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table

GRACE_PERIOD = 1800


def _synchronise_tables_for_connector(connector: Connector, bq_ids: List[str]):

    # DELETE tables that should no longer exist in bigquery, as fivetran does not
    # delete for us. It will cascade onto bigquery as well.

    for table in connector.integration.table_set.all():
        if table.bq_id not in bq_ids:
            table.delete()

    # CREATE tables to map new tables in bigquery

    create_bq_ids = bq_ids - connector.integration.bq_ids

    if len(create_bq_ids) > 0:

        tables = [
            Table(
                source=Table.Source.INTEGRATION,
                bq_table=bq_id.split(".")[0],
                bq_dataset=bq_id.split(".")[1],
                project=connector.integration.project,
                integration=connector.integration,
            )
            for bq_id in create_bq_ids
        ]

        with transaction.atomic():
            # this will fail with unique constraint error if there is a concurrent job
            Table.objects.bulk_create(tables)

    # UPDATE all tables with statistics from bigquery

    for table in tables:
        table.update_num_rows()

    # re-calculate total rows after tables are updated
    connector.integration.project.team.update_row_count()


def start_connector_sync(connector: Connector):

    if connector.is_historical_sync:
        clients.fivetran().start_initial_sync(connector)
    elif not connector.can_skip_resync:
        clients.fivetran().start_update_sync(connector)

    connector.fivetran_sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()


def end_connector_sync(connector, is_initial):

    # handle syncing fivetran connector, either via polling or user interaction
    # - check at least one table is available in bigquery
    #   - error for event style connectors (webhooks and event_tracking)
    #   - 30 minute grace period for the other connectors due to issues with fivetran
    # - synchronize the tables in bigquery to our database
    # - [optionally] send an email

    connector.sync_updates_from_fivetran()

    integration = connector.integration
    bq_ids = connector.schema_obj.get_bq_ids()

    # none of the fivetran tables are available in bigquery yet
    if is_initial and len(bq_ids) == 0:

        # - event_tracking and webhooks: user did not send any data yet
        # - otherwise: issues with fivetran, keep a 30 minute grace period for it to fix itself

        grace_period_elapsed = (
            timezone.now() - connector.succeeded_at
        ).total_seconds() > GRACE_PERIOD

        if connector.conf.service_is_dynamic or grace_period_elapsed:
            integration.state = Integration.State.ERROR
            integration.save()

        return

    _synchronise_tables_for_connector(connector, bq_ids)

    integration.state = Integration.State.DONE
    integration.save()

    if integration.created_by and is_initial:

        email = integration_ready_email(integration, integration.created_by)
        email.send()

        time_to_sync = (
            connector.succeeded - connector.fivetran_sync_started
        ).total_seconds()

        analytics.track(
            integration.created_by.id,
            INTEGRATION_SYNC_SUCCESS_EVENT,
            {
                "id": integration.id,
                "kind": integration.kind,
                "row_count": integration.num_rows,
                "time_to_sync": int(time_to_sync),
            },
        )
