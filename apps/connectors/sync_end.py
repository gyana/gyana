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

    # check a syncing connector for errors, check the bigquery entities exist,
    # handle various error states if they don't, and finally map the table
    # information into postgres

    integration = connector.integration

    fivetran_obj = clients.fivetran().get(connector)
    status = fivetran_obj.status
    setup_state = status.setup_state

    if setup_state != "connected":
        integration.state = Integration.State.ERROR
        integration.save()
        return

    has_completed_sync = not (
        status.is_historical_sync or status.sync_state == "syncing"
    )

    if not has_completed_sync:
        return

    schema_obj = clients.fivetran().get_schemas(connector)

    # a list of all bigquery ids that (1) are available in bigquery and
    # (2) are enabled in the fivetran schema object (optional)
    bq_ids = schema_obj.get_bq_ids()

    # it is possible that fivetran reports the connector sync completed,
    # but there are no tables in bigquery - this could either happen if they
    # give us the wrong information, or for certain connectors where tables
    # are added dynamically, and there are none initially (e.g. Segment)
    if len(bq_ids) == 0:

        dynamic_has_failed = connector.conf.service_type in [
            ServiceTypeEnum.EVENT_TRACKING,
            ServiceTypeEnum.WEBHOOKS,
        ]
        static_has_failed = (
            timezone.now() - fivetran_obj.succeeded_at
        ).total_seconds > 1800

        # for webhooks and event_tracking, alert the user that events are not received yet
        if dynamic_has_failed or static_has_failed:
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
