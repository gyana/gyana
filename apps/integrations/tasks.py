import time
from datetime import datetime
from functools import reduce

import analytics
from apps.integrations.bigquery import get_tables_in_dataset, sync_table
from apps.tables.models import Table
from apps.utils.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
from google.api_core.exceptions import GoogleAPICallError
from apps.utils.clients import DATASET_ID

from .fivetran import FivetranClient
from .models import Integration


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


@shared_task(bind=True)
def file_sync(self, file: str, project_id: int):
    """
    Task syncs a file into bigquery. On success it

    :returns: Tuple(table.id, elapsed_time)
    """
    # 1. Create table to track progress in
    table = Table(
        source=Table.Source.INTEGRATION,
        bq_dataset=DATASET_ID,
        project_id=project_id,
        num_rows=0,
    )
    table.save()

    # We keep track of timing
    sync_start_time = time.time()

    # 2. Sync the file into BigQuery
    sync_generator = sync_table(table=table, file=file, kind=Integration.Kind.CSV)
    query_job = next(sync_generator)

    # 3. Record progress on the sync
    progress_recorder = ProgressRecorder(self)

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

    # 4. Let the rest of the generator run, if the sync is successful this yields.
    # Otherwise it raises
    try:
        next(sync_generator)
    except (GoogleAPICallError, TimeoutError) as e:
        # If our bigquery sync failed we also delete the table to avoid dangling entities
        table.delete()
        raise e

    sync_end_time = time.time()

    return (table.id, int(sync_end_time - sync_start_time))


@shared_task(bind=True)
def send_integration_email(self, integration_id: int, time_elapsed: int):
    integration = get_object_or_404(Integration, pk=integration_id)

    url = reverse(
        "project_integrations:detail",
        args=(
            integration.project.id,
            integration_id,
        ),
    )

    creator = integration.created_by

    if integration.enable_sync_emails:
        message = EmailMessage(
            subject=None,
            from_email="Gyana Notifications <notifications@gyana.com>",
            to=[creator.email],
        )
        # This id points to the sync success template in SendGrid
        message.template_id = "d-5f87a7f6603b44e09b21cfdcf6514ffa"
        message.merge_data = {
            creator.email: {
                "userName": creator.first_name or creator.email.split("@")[0],
                "integrationName": integration.name,
                "integrationHref": settings.EXTERNAL_URL + url,
                "projectName": integration.project.name,
            }
        }
        message.esp_extra = {
            "asm": {
                # The "App Notifications" Unsubscribe group
                "group_id": 17220,
            },
        }
        message.send()

    analytics.track(
        creator.id,
        INTEGRATION_SYNC_SUCCESS_EVENT,
        {
            "id": integration.id,
            "kind": integration.kind,
            "row_count": integration.num_rows,
            "time_to_sync": time_elapsed,
        },
    )

    return integration_id


@shared_task(bind=True)
def run_sheets_sync(self, integration_id):
    integration = get_object_or_404(Integration, pk=integration_id)

    if not integration.table_set.exists():
        table = Table(
            source=Table.Source.INTEGRATION,
            bq_dataset=DATASET_ID,
            project=integration.project,
            integration=integration,
            num_rows=0,
        )
        table.save()
    else:
        table = integration.table_set.first()

    # We track the time it takes to sync for our analytics
    sync_start_time = time.time()

    progress_recorder = ProgressRecorder(self)

    sync_generator = sync_table(
        table=table,
        url=integration.url,
        cell_range=integration.cell_range,
        kind=Integration.Kind.GOOGLE_SHEETS,
    )
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

    sync_end_time = time.time()

    integration.last_synced = datetime.now()
    integration.save()

    url = reverse(
        "project_integrations:detail",
        args=(
            integration.project.id,
            integration_id,
        ),
    )

    creator = integration.created_by

    if integration.enable_sync_emails:
        message = EmailMessage(
            subject=None,
            from_email="Gyana Notifications <notifications@gyana.com>",
            to=[creator.email],
        )
        # This id points to the sync success template in SendGrid
        message.template_id = "d-5f87a7f6603b44e09b21cfdcf6514ffa"
        message.merge_data = {
            creator.email: {
                "userName": creator.first_name or creator.email.split("@")[0],
                "integrationName": integration.name,
                "integrationHref": settings.EXTERNAL_URL + url,
                "projectName": integration.project.name,
            }
        }
        message.esp_extra = {
            "asm": {
                # The "App Notifications" Unsubscribe group
                "group_id": 17220,
            },
        }
        message.send()

    analytics.track(
        creator.id,
        INTEGRATION_SYNC_SUCCESS_EVENT,
        {
            "id": integration.id,
            "kind": integration.kind,
            "row_count": integration.num_rows,
            "time_to_sync": int(sync_end_time - sync_start_time),
        },
    )

    return integration_id
