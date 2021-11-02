import analytics
from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.connectors.bigquery import get_bq_tables_from_connector
from apps.connectors.models import Connector
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table

from .fivetran.schema import get_bq_ids_from_schemas


def get_table_from_bq_id(bq_id, connector):
    dataset_id, table_id = bq_id.split(".")
    return Table(
        source=Table.Source.INTEGRATION,
        bq_table=table_id,
        bq_dataset=dataset_id,
        project=connector.integration.project,
        integration=connector.integration,
    )


def complete_connector_sync(connector: Connector):
    integration = connector.integration
    initial_sync = integration.table_set.count() == 0

    schema_obj = clients.fivetran().get_schemas(connector)

    # a list of all bigquery ids that (1) are available in bigquery and
    # (2) are enabled in the fivetran schema object (optional)
    bq_ids = schema_obj.get_bq_ids()

    # it is possible that fivetran reports the connector sync completed,
    # but there are no tables in bigquery - this could either happen if they
    # give us the wrong information, or for certain connectors where tables
    # are added dynamically, and there are none initially (e.g. Segment)
    if len(bq_ids) == 0:
        return

    # calculate the *new* tables that should be added to database and
    # map them onto tables in our database
    new_bq_ids = bq_ids - {t.bq_id for t in integration.table_set.all()}
    tables = [get_table_from_bq_id(bq_id, connector) for bq_id in new_bq_ids]

    with transaction.atomic():
        # this will fail with unique constraint error if there is a concurrent job
        Table.objects.bulk_create(tables)

        for table in tables:
            table.update_num_rows()

        integration.state = Integration.State.DONE
        integration.save()

    if integration.created_by and initial_sync:

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


def delete_tables_not_in_schema(connector: Connector):
    # if we've deleted tables, we'll need to delete them from BigQuery

    tables = connector.integration.table_set.all()
    schema_bq_ids = get_bq_ids_from_schemas(connector)

    for table in tables:
        if table.bq_id not in schema_bq_ids:
            table.delete()

    # re-calculate total rows after tables are deleted
    connector.integration.project.team.update_row_count()


def check_new_tables_added_to_schema(connector: Connector):
    # if we've added new tables, we need to trigger resync
    # otherwise, we don't want to make the user wait

    bq_ids = {t.bq_id for t in connector.integration.table_set.all()}
    schema_bq_ids = set(get_bq_ids_from_schemas(connector))

    return len(schema_bq_ids - bq_ids) > 0


def run_connector_sync(connector: Connector):

    is_initial_sync = requires_sync = connector.integration.table_set.count() == 0

    # after initial sync is done, a resync is required if the user added new tables
    # but not if they only deleted tables

    if not is_initial_sync:
        delete_tables_not_in_schema(connector)
        requires_sync = check_new_tables_added_to_schema(connector)

    if requires_sync:
        clients.fivetran().start_initial_sync(connector)

        connector.fivetran_sync_started = timezone.now()
        connector.save()

        connector.integration.state = Integration.State.LOAD
        connector.integration.save()
