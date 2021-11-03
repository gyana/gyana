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


def _get_table_from_bq_id(bq_id, connector):
    dataset_id, table_id = bq_id.split(".")
    return Table(
        source=Table.Source.INTEGRATION,
        bq_table=table_id,
        bq_dataset=dataset_id,
        project=connector.integration.project,
        integration=connector.integration,
    )


def _synchronise_tables_for_connector(connector: Connector, bq_ids: List[str]):

    # DELETE tables that should no longer exist in bigquery
    # (fivetran does not delete for us - it will cascade onto bigquery as well)
    #
    # CREATE tables to map new tables in bigquery

    for table in connector.integration.table_set.all():
        if table.bq_id not in bq_ids:
            table.delete()

    create_bq_ids = bq_ids - connector.integration.bq_ids

    if len(create_bq_ids) > 0:

        tables = [_get_table_from_bq_id(bq_id, connector) for bq_id in create_bq_ids]

        with transaction.atomic():
            # this will fail with unique constraint error if there is a concurrent job
            Table.objects.bulk_create(tables)

            for table in tables:
                table.update_num_rows()

    # re-calculate total rows after tables are updated
    connector.integration.project.team.update_row_count()


def _check_new_tables(connector: Connector):
    bq_ids = clients.fivetran().get_schemas(connector).enabled_bq_ids
    return len(bq_ids - connector.integration.bq_ids) > 0


def start_connector_sync(connector: Connector):

    fivetran_obj = clients.fivetran().get(connector)

    if fivetran_obj.status.is_historical_sync:
        clients.fivetran().start_initial_sync(connector)
    else:
        # it is possible to skip a resync if no new tables are added and the
        # connector uses a known schema object
        if not connector.conf.service_uses_schema or _check_new_tables(connector):
            clients.fivetran().start_update_sync(connector)

    connector.fivetran_sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()


def handle_syncing_connector(connector):

    # handle syncing fivetran connector, either via polling or user interaction
    # - validate the setup state is "connected"
    # - check historical sync is completed
    # - check at least one table is available in bigquery
    #   - error for event style connectors (webhooks and event_tracking)
    #   - 30 minute grace period for the other connectors due to issues with fivetran
    # - synchronize the tables in bigquery to our database
    # - [optionally] send an email

    integration = connector.integration
    fivetran_obj = clients.fivetran().get(connector)

    # fivetran setup is broken or incomplete
    if fivetran_obj.status.setup_state != "connected":
        integration.state = Integration.State.ERROR
        integration.save()

    # the historical or incremental sync is ongoing
    elif fivetran_obj.status.is_syncing:
        pass

    # none of the fivetran tables are available in bigquery yet
    elif len(bq_ids := clients.fivetran().get_schemas(connector).get_bq_ids()) == 0:

        # - event_tracking and webhooks: user did not send any data yet
        # - otherwise: issues with fivetran, keep a 30 minute grace period for it to fix itself

        grace_period_elapsed = (
            timezone.now() - fivetran_obj.succeeded_at
        ).total_seconds() > GRACE_PERIOD

        if connector.conf.service_is_dynamic or grace_period_elapsed:
            integration.state = Integration.State.ERROR
            integration.save()

    else:

        send_email = integration.table_set.count() == 0

        _synchronise_tables_for_connector(connector, bq_ids)

        integration.state = Integration.State.DONE
        integration.save()

        if integration.created_by and send_email:

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
