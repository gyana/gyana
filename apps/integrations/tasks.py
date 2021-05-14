from apps.integrations.bigquery import get_tables_in_dataset, sync_integration
from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .fivetran import FivetranClient
from .models import Integration


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, integration_id):

    integration = get_object_or_404(Integration, pk=integration_id)

    FivetranClient(integration).block_until_synced()
    get_tables_in_dataset(integration)

    url = reverse(
        "projects:integrations:detail",
        args=(
            integration.project.id,
            integration_id,
        ),
    )

    send_mail(
        "Ready",
        f"Your integration has completed the initial sync - click here {url}",
        "Anymail Sender <from@example.com>",
        ["to@example.com"],
    )

    return integration_id


@shared_task(bind=True)
def run_external_table_sync(self, integration_id):

    integration = get_object_or_404(Integration, pk=integration_id)

    sync_integration(integration)

    url = reverse(
        "projects:integrations:detail",
        args=(
            integration.project.id,
            integration_id,
        ),
    )

    send_mail(
        "Ready",
        f"Your integration has completed the initial sync - click here {url}",
        "Anymail Sender <from@example.com>",
        ["to@example.com"],
    )

    return integration_id
