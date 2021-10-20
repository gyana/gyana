from datetime import datetime

from celery import shared_task
from django.utils import timezone

from apps.base.clients import fivetran_client
from apps.base.tasks import honeybadger_check_in
from apps.integrations.models import Integration
from apps.tables.models import Table

from .fivetran.client import FivetranClientError
from .models import Connector
from .tasks import complete_connector_sync

FIVETRAN_SYNC_FREQUENCY_HOURS = 6
FIVETRAN_CHECK_SYNC_TIMEOUT_HOURS = 24


def update_fivetran_succeeded_at(connector: Connector, succeeded_at: str):
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
            if data["succeeded_at"] is not None:
                update_fivetran_succeeded_at(connector, data["succeeded_at"])
        except FivetranClientError:
            pass

    honeybadger_check_in("ZbIlqq")


@shared_task
def check_syncing_connectors_from_fivetran():

    sync_started_after = timezone.now() - timezone.timedelta(
        hours=FIVETRAN_CHECK_SYNC_TIMEOUT_HOURS
    )

    connectors_to_check = Connector.objects.filter(
        integration__state=Integration.State.LOAD, sync_started_gt=sync_started_after
    )

    for connector in connectors_to_check:
        if fivetran_client().has_completed_sync(connector):
            complete_connector_sync(connector)
