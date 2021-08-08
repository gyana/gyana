import textwrap
import time
from datetime import datetime
from functools import reduce

import analytics
from apps.base.clients import DATASET_ID
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.sheets.bigquery import (
    get_last_modified_from_drive_file,
    get_metadata_from_sheet,
    import_table_from_sheet,
)
from apps.tables.models import Table
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.db import transaction
from django.shortcuts import get_object_or_404

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

        sheet.drive_file_last_modified = get_last_modified_from_drive_file(sheet)

        progress_recorder = ProgressRecorder(self)

        query_job = import_table_from_sheet(table=table, sheet=sheet)

        while query_job.running():
            current, total = _calc_progress(query_job.query_plan)
            progress_recorder.set_progress(current, total)
            time.sleep(0.5)

        progress_recorder.set_progress(*_calc_progress(query_job.query_plan))

        # capture external table creation errors

        if query_job.exception():
            raise Exception(query_job.errors[0]["message"])

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
        table.num_rows = table.bq_obj.num_rows
        table.data_updated = datetime.now()
        table.save()

        sheet.integration = integration
        sheet.last_synced = datetime.now()
        sheet.save()

    # the initial sync completed successfully and a new integration is created

    if created_by := integration.sheet.created_by:

        email = integration_ready_email(integration, created_by)
        email.send()

        analytics.track(
            created_by.id,
            INTEGRATION_SYNC_SUCCESS_EVENT,
            {
                "id": integration.id,
                "kind": integration.kind,
                "row_count": integration.num_rows,
                "time_to_sync": int(
                    (query_job.ended - query_job.started).total_seconds()
                ),
            },
        )

    return integration.id
