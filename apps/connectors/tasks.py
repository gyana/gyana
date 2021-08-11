from apps.base.clients import fivetran_client
from apps.connectors.models import Connector
from apps.integrations.models import Integration
from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .bigquery import get_tables_in_dataset


@shared_task(bind=True)
def poll_fivetran_historical_sync(self, integration_id):

    integration = get_object_or_404(Integration, pk=integration_id)

    fivetran_client().block_until_synced(integration)
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


def run_connector_sync(connector: Connector):

    fivetran_client().start(connector)

    task = poll_fivetran_historical_sync.delay(connector.integration.id)

    result = task.delay(connector.id)
    connector.sync_task_id = result.task_id
    connector.sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()
