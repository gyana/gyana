import textwrap
import time
from datetime import datetime
from functools import reduce

import analytics
from apps.base.clients import DATASET_ID
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.bigquery import import_table_from_external_config
from apps.integrations.models import Integration
from apps.sheets.bigquery import create_external_sheets_config, get_metadata_from_sheet
from apps.tables.models import Table
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Sheet


def _calc_progress(jobs):
    return reduce(
        lambda tpl, curr: (
            # We only keep track of completed states for now, not failed states
            tpl[0] + (1 if curr.status == "COMPLETE" else 0),
            tpl[1] + 1,
        ),
        jobs,
        (0, 0),
    )


def _send_update(integration: Integration, time_to_sync: int):

    creator = integration.sheet.creator

    if creator:

        url = reverse(
            "project_integrations:detail",
            args=(
                integration.project.id,
                integration.id,
            ),
        )

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
            "time_to_sync": time_to_sync,
        },
    )


@shared_task(bind=True)
def run_sheets_sync(self, sheet_id):
    sheet = get_object_or_404(Sheet, pk=sheet_id)

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    with transaction.atomic():

        if not sheet.integration:
            table = Table(
                source=Table.Source.INTEGRATION,
                bq_dataset=DATASET_ID,
                project=sheet.project,
                num_rows=0,
            )
            table.save()
        else:
            table = sheet.integration.table_set.first()

        # we track the time it takes to sync for our analytics
        sync_start_time = time.time()

        progress_recorder = ProgressRecorder(self)

        external_config = create_external_sheets_config(sheet.url, sheet.cell_range)
        sync_generator = import_table_from_external_config(
            table=table, external_config=external_config
        )
        query_job = next(sync_generator)

        while query_job.running():
            current, total = _calc_progress(query_job.query_plan)
            progress_recorder.set_progress(current, total)
            time.sleep(0.5)

        progress_recorder.set_progress(*_calc_progress(query_job.query_plan))

        # The next yield happens when the sync has finalised, only then we finish this task
        next(sync_generator)

        sync_end_time = time.time()

        title = get_metadata_from_sheet(sheet)["properties"]["title"]
        # maximum Google Drive name length is 32767
        name = textwrap.shorten(title, width=255, placeholder="...")

        integration = Integration(
            name=name,
            project=sheet.project,
            kind=Integration.Kind.SHEET,
        )
        integration.save()

        table.integration = integration
        table.save()

        sheet.integration = integration
        sheet.last_synced = datetime.now()
        sheet.save()

    # the initial sync completed successfully and a new integration is created

    _send_update(integration, int(sync_end_time - sync_start_time))

    return integration.id
