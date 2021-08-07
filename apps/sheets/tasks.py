import time
from datetime import datetime
from functools import reduce

import analytics
from apps.base.clients import DATASET_ID
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.bigquery import sync_table
from apps.integrations.models import Integration
from apps.tables.models import Table
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.urls import reverse


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
        url=integration.sheet.url,
        cell_range=integration.sheet.cell_range,
        kind=Integration.Kind.SHEET,
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

    integration.sheet.last_synced = datetime.now()
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
