from typing import List

import analytics
from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.connectors.fivetran.config import ServiceTypeEnum
from apps.connectors.models import Connector
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table


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
    if fivetran_obj.is_syncing:
        return

    bq_ids = clients.fivetran().get_schemas(connector).get_bq_ids()

    # none of the fivetran tables are available in bigquery yet
    if len(bq_ids) == 0:

        has_failed = (
            connector.conf.service_is_dynamic
            or (timezone.now() - fivetran_obj.succeeded_at).total_seconds > 1800
        )

        if has_failed:
            integration.state = Integration.State.ERROR
            integration.save()

        return

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
