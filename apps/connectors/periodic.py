from celery import shared_task

from apps.base import clients
from apps.base.tasks import honeybadger_check_in

from .fivetran.client import FivetranClientError
from .models import Connector
from .sync import handle_syncing_connector


@shared_task
def update_connectors_from_fivetran():

    connectors_to_check = Connector.objects.needs_periodic_sync_check()

    for connector in connectors_to_check:
        try:
            succeeded_at = clients.fivetran().get(connector).succeeded_at
            if succeeded_at is not None:
                connector.update_fivetran_succeeded_at(succeeded_at)
                # update any newly created tables
                handle_syncing_connector(connector)

        except FivetranClientError:
            pass

    honeybadger_check_in("ZbIlqq")


@shared_task
def check_syncing_connectors_from_fivetran():

    connectors_to_check = Connector.objects.needs_initial_sync_check()

    for connector in connectors_to_check:
        handle_syncing_connector(connector)

    honeybadger_check_in("VBInlo")
