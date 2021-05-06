from apps.connector.models import Connector
from celery import shared_task
from django.shortcuts import get_object_or_404
from lib.fivetran import FivetranClient


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, connector_id):

    connector = get_object_or_404(Connector, pk=connector_id)

    FivetranClient(connector).block_until_synced()

    for report in connector.reports.all():
        if report.connectors_ready():
            report.notify()

    return connector_id
