from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
from lib.fivetran import FivetranClient

from .models import Integration


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, connector_id):

    integration = get_object_or_404(Integration, pk=connector_id)

    FivetranClient(integration).block_until_synced()

    url = reverse(
        "projects:integrations:detail",
        args=(
            integration.project.id,
            connector_id,
        ),
    )

    send_mail(
        "Ready",
        f"Your integration has completed the initial sync - click here {url}",
        "Anymail Sender <from@example.com>",
        ["to@example.com"],
    )

    return connector_id
