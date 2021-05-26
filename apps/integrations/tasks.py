import time
from functools import reduce

from apps.integrations.bigquery import get_tables_in_dataset, sync_integration
from celery import shared_task
from celery_progress.backend import ProgressRecorder
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

    progress_recorder = ProgressRecorder(self)
    sync_generator = sync_integration(integration)
    query_job = next(sync_generator)

    def calc_progress(jobs):
        return reduce(
            lambda tpl, curr: (
                # We only keep track of completed states for now, not failed states
                tpl[0] + (1 if curr.status == "COMPLETE" else 0),
                tpl[1] + 1,
            ),
            jobs,
            (0, 0),
        )

    while query_job.running():
        current, total = calc_progress(query_job.query_plan)
        progress_recorder.set_progress(current, total)
        time.sleep(0.5)

    progress_recorder.set_progress(*calc_progress(query_job.query_plan))

    # The next yield happens when the sync has finalised, only then we finish this task
    next(sync_generator)

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
