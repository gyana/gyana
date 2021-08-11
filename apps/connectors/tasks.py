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
def poll_fivetran_historical_sync(self, connector_id):

    connector = get_object_or_404(Connector, pk=connector_id)

    fivetran_client().block_until_synced(connector)
    get_tables_in_dataset(connector)

    integration = connector.integration

    integration.state = Integration.State.DONE
    integration.save()

    url = reverse(
        "project_integrations:detail",
        args=(
            integration.project.id,
            integration.id,
        ),
    )

    send_mail(
        "Ready",
        f"Your integration has completed the initial sync - click here {url}",
        "Anymail Sender <from@example.com>",
        ["to@example.com"],
    )

    return integration.id


def run_connector_sync(connector: Connector):

    fivetran_client().start(connector)

    task = poll_fivetran_historical_sync.delay(connector.integration.id)

    result = task.delay(connector.id)
    connector.sync_task_id = result.task_id
    connector.sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()
