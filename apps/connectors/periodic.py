from celery import shared_task
from honeybadger import honeybadger

from apps.base.tasks import honeybadger_check_in

from .fivetran.client import FivetranClientError
from .models import Connector


@shared_task
def sync_all_updates_from_fivetran():
    try:
        Connector.sync_all_updates_from_fivetran()
    except FivetranClientError as exc:
        honeybadger.notify(exc)

    honeybadger_check_in("ZbIlqq")
