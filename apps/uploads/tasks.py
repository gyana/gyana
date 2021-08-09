import time
from functools import reduce

import analytics
from apps.base.clients import DATASET_ID
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table
from apps.uploads.bigquery import import_table_from_upload
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Upload


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


def _do_sync_with_progress(task, upload, table):

    progress_recorder = ProgressRecorder(task)

    load_job = import_table_from_upload(table=table, upload=upload)

    while load_job.running():
        current, total = _calc_progress(load_job.query_plan)
        progress_recorder.set_progress(current, total)
        time.sleep(0.5)

    progress_recorder.set_progress(*_calc_progress(load_job.query_plan))

    # capture external table creation errors

    if load_job.exception():
        raise Exception(load_job.errors[0]["message"])

    table.num_rows = table.bq_obj.num_rows
    table.data_updated = timezone.now()
    table.save()

    upload.last_synced = timezone.now()
    upload.save()

    return load_job


@shared_task(bind=True)
def run_initial_upload_sync(self, upload_id: int):

    upload = get_object_or_404(Upload, pk=upload_id)

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    with transaction.atomic():

        integration = Integration(
            name="TODO",
            project=upload.project,
            kind=Integration.Kind.SHEET,
        )
        integration.save()

        table = Table(
            integration=integration,
            source=Table.Source.INTEGRATION,
            bq_dataset=DATASET_ID,
            project=upload.project,
            num_rows=0,
        )
        upload.integration = integration
        table.save()

        load_job = _do_sync_with_progress(self, upload, table)

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
                    (load_job.ended - load_job.started).total_seconds()
                ),
            },
        )

    return integration.id
