from apps.integrations.models import Integration
from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .bigquery import get_tables_in_dataset
from .fivetran import FivetranClient


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, integration_id):

    integration = get_object_or_404(Integration, pk=integration_id)

    FivetranClient().block_until_synced(integration)
    get_tables_in_dataset(integration)

    url = reverse(
        "project_integrations:detail",
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
def update_integration_fivetran_schema(self, fivetran_id, updated_checkboxes):
    FivetranClient().update_schema(fivetran_id, updated_checkboxes)

    return


@shared_task(bind=True)
def start_fivetran_integration_task(self, fivetran_id):
    FivetranClient().start(fivetran_id)

    return
