import analytics
from apps.base.clients import DATASET_ID
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table
from apps.uploads.bigquery import import_table_from_upload
from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Upload


def _do_sync(upload, table):

    load_job = import_table_from_upload(table=table, upload=upload)

    if load_job.exception():
        raise Exception(load_job.errors[0]["message"])

    table.num_rows = table.bq_obj.num_rows
    table.data_updated = timezone.now()
    table.save()

    upload.last_synced = timezone.now()
    upload.save()

    return load_job


@shared_task(bind=True)
def run_upload_sync_task(self, upload_id: int):

    upload = get_object_or_404(Upload, pk=upload_id)
    integration = upload.integration

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    try:

        with transaction.atomic():

            table, created = Table.objects.get_or_create(
                integration=integration,
                source=Table.Source.INTEGRATION,
                bq_dataset=DATASET_ID,
                project=integration.project,
            )

            # no progress as load job does not provide query plan
            load_job = _do_sync(upload, table)

            integration.state = Integration.State.DONE
            integration.save()

    except Exception as e:
        integration.state = Integration.State.ERROR
        integration.save()
        raise e

    # the initial sync completed successfully and a new integration is created

    if (created_by := integration.created_by) and created:

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


def run_upload_sync(upload: Upload):

    result = run_upload_sync_task.delay(upload.id)
    upload.sync_task_id = result.task_id
    upload.sync_started = timezone.now()
    upload.save()

    upload.integration.state = Integration.State.LOAD
    upload.integration.save()
