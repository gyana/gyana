from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from honeybadger import honeybadger

from apps.base import clients
from apps.connectors.fivetran.client import FivetranClientError

from .bigquery import delete_connector_datasets
from .models import Connector


@receiver(post_delete, sender=Connector)
def delete_fivetran_connector(sender, instance, *args, **kwargs):
    if settings.MOCK_REMOTE_OBJECT_DELETION:
        return

    delete_connector_datasets(instance)

    try:
        clients.fivetran().delete(instance)
    except FivetranClientError as exc:
        honeybadger.notify(exc)
