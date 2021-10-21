from celery import shared_task

from apps.base.clients import fivetran_client
from apps.base.tasks import honeybadger_check_in

from .fivetran.client import FivetranClientError
from .models import Connector
from .tasks import complete_connector_sync


@shared_task
def update_connectors_from_fivetran():

    connectors_to_check = Connector.objects.needs_periodic_sync_check()

    for connector in connectors_to_check:
        try:
            succeeded_at = fivetran_client().get(connector).get("succeeded_at")
            if succeeded_at is not None:
                connector.update_fivetran_succeeded_at(connector, succeeded_at)

        except FivetranClientError:
            pass

    honeybadger_check_in("ZbIlqq")


@shared_task
def check_syncing_connectors_from_fivetran():

    connectors_to_check = Connector.objects.needs_initial_sync_check()

    for connector in connectors_to_check:
        if fivetran_client().has_completed_sync(connector):
            complete_connector_sync(connector)
