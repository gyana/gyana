from apps.connectors.models import Connector
from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
from lib.fivetran import FivetranClient


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, connector_id):

    connector = get_object_or_404(Connector, pk=connector_id)

    FivetranClient(connector).block_until_synced()

    url = reverse(
        "projects:connectors:detail",
        args=(
            connector.project.id,
            connector_id,
        ),
    )

    send_mail(
        "Ready",
        f"Your connector has completed the initial sync - click here {url}",
        "Anymail Sender <from@example.com>",
        ["to@example.com"],
    )

    return connector_id
