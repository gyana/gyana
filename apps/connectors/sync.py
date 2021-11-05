from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.connectors.models import Connector
from apps.integrations.emails import send_integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table

GRACE_PERIOD = 1800


def _sync_tables_for_connector(connector: Connector):

    # DELETE tables that should no longer exist in bigquery, as fivetran does not
    # delete for us. It will cascade onto bigquery as well.

    for table in connector.integration.table_set.all():
        if table.bq_id not in connector.actual_bq_ids:
            table.delete()

    # CREATE tables to map new tables in bigquery

    new_bq_ids = connector.actual_bq_ids - connector.synced_bq_ids

    if len(new_bq_ids) > 0:

        tables = [
            Table(
                source=Table.Source.INTEGRATION,
                bq_dataset=bq_id.split(".")[0],
                bq_table=bq_id.split(".")[1],
                project=connector.integration.project,
                integration=connector.integration,
            )
            for bq_id in new_bq_ids
        ]

        with transaction.atomic():
            # this will fail with unique constraint error if there is a concurrent job
            Table.objects.bulk_create(tables)

    # UPDATE all tables with statistics from bigquery

    for table in connector.integration.table_set.all():
        table.sync_updates_from_bigquery()

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


def end_connector_sync(connector, is_initial=False):

    # handle syncing fivetran connector, either via polling or user interaction
    # - check at least one table is available in bigquery
    #   - error for event style connectors (webhooks and event_tracking)
    #   - 30 minute grace period for the other connectors due to issues with fivetran
    # - synchronize the tables in bigquery to our database

    if is_initial and len(connector.actual_bq_ids) == 0:

        grace_period_elapsed = (
            timezone.now() - connector.succeeded_at
        ).total_seconds() > GRACE_PERIOD

        if connector.conf.service_is_dynamic or grace_period_elapsed:
            connector.integration.state = Integration.State.ERROR
            connector.integration.save()

        return

    _sync_tables_for_connector(connector)

    connector.integration.state = Integration.State.DONE
    connector.integration.save()

    connector.bigquery_succeeded_at = connector.succeeded_at
    connector.save()

    if is_initial:
        send_integration_ready_email(connector.integration)
