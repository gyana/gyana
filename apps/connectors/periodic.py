from celery import shared_task
from honeybadger import honeybadger

from apps.base.tasks import honeybadger_check_in

from .fivetran.client import FivetranClientError
from .models import Connector

# Timeout after 10 minutes, for the new task to start. Tasks are idempotent and
# commit for each connector, so there is no loss in data and this way we avoid
# task congestion.


@shared_task(timeout=600)
def sync_all_updates_from_fivetran():
    try:
        Connector.sync_all_updates_from_fivetran()
    except FivetranClientError as exc:
        honeybadger.notify(exc)

    honeybadger_check_in("ZbIlqq")
