import time
from datetime import datetime
from functools import reduce

import analytics
from apps.base.clients import DATASET_ID
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .bigquery import get_last_modified_from_drive_file, import_table_from_sheet
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


def _do_sync_with_progress(task, sheet, table):

    sheet.drive_file_last_modified = get_last_modified_from_drive_file(sheet)

    progress_recorder = ProgressRecorder(task)

    query_job = import_table_from_sheet(table=table, sheet=sheet)

    while query_job.running():
        current, total = _calc_progress(query_job.query_plan)
        progress_recorder.set_progress(current, total)
        time.sleep(0.5)

    progress_recorder.set_progress(*_calc_progress(query_job.query_plan))

    # capture external table creation errors

    if query_job.exception():
        raise Exception(query_job.errors[0]["message"])

    table.num_rows = table.bq_obj.num_rows
    table.data_updated = datetime.now()
    table.save()

    sheet.last_synced = datetime.now()
    sheet.save()

    return query_job


@shared_task(bind=True)
def run_initial_sheets_sync(self, sheet_id):
    sheet = get_object_or_404(Sheet, pk=sheet_id)
    integration = sheet.integration

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    try:

        with transaction.atomic():

            table = Table(
                integration=integration,
                source=Table.Source.INTEGRATION,
                bq_dataset=DATASET_ID,
                project=integration.project,
                num_rows=0,
            )
            sheet.integration = integration
            table.save()

            query_job = _do_sync_with_progress(self, sheet, table)

    except Exception as e:
        integration.state = Integration.State.ERROR
        integration.save()
        raise e

    integration.state = Integration.State.DONE
    integration.save()

    # the initial sync completed successfully and a new integration is created

    if created_by := integration.created_by:

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


@shared_task(bind=True)
def run_update_sheets_sync(self, sheet_id):
    sheet = get_object_or_404(Sheet, pk=sheet_id)

    integration = sheet.integration
    table = integration.table_set.first()

    try:

        with transaction.atomic():
            _do_sync_with_progress(self, sheet, table)

    except Exception as e:
        integration.state = Integration.State.ERROR
        integration.save()
        raise e

    integration.state = Integration.State.DONE
    integration.save()

    return integration.id


def run_sheets_sync(sheet: Sheet):

    task = (
        run_initial_sheets_sync
        if sheet.integration.table_set.count() == 0
        else run_update_sheets_sync
    )

    result = task.delay(sheet.id)
    sheet.sync_task_id = result.task_id
    sheet.sync_started = timezone.now()
    sheet.save()

    sheet.integration.state = Integration.State.LOAD
    sheet.integration.save()
