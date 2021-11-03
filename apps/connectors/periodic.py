from celery import shared_task

from apps.base.tasks import honeybadger_check_in

from .fivetran.client import FivetranClientError
from .models import Connector


@shared_task
def update_connectors_from_fivetran():
    connectors_to_check = Connector.objects.needs_periodic_sync_check()

    for connector in connectors_to_check:
        try:
            connector.sync_updates_from_fivetran()
        except FivetranClientError:
            pass

    honeybadger_check_in("ZbIlqq")


@shared_task
def check_syncing_connectors_from_fivetran():
    connectors_to_check = Connector.objects.needs_initial_sync_check()

    for connector in connectors_to_check:
        try:
            connector.sync_updates_from_fivetran()
        except FivetranClientError:
            pass

    honeybadger_check_in("VBInlo")
