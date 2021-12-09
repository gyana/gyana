from uuid import uuid4

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.base.time import catchtime
from apps.integrations.emails import send_integration_ready_email
from apps.runs.models import JobRun
from apps.tables.models import Table
from apps.uploads.bigquery import import_table_from_upload
from apps.users.models import CustomUser

from .models import Upload


@shared_task(bind=True)
def run_upload_sync_task(self, run_id: int):

    run = JobRun.objects.get(pk=run_id)
    integration = run.integration
    upload = integration.upload

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    with transaction.atomic():

        table, created = Table.objects.get_or_create(
            integration=integration,
            source=Table.Source.INTEGRATION,
            bq_table=upload.table_id,
            bq_dataset=integration.project.team.tables_dataset_id,
            project=integration.project,
        )

        with catchtime() as get_time_to_sync:
            import_table_from_upload(table=table, upload=upload)

        table.sync_updates_from_bigquery()

    if created:
        send_integration_ready_email(integration, int(get_time_to_sync()))

    return integration.id


def run_upload_sync(upload: Upload, user: CustomUser):
    run = JobRun.objects.create(
        source=JobRun.Source.INTEGRATION,
        integration=upload.integration,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_upload_sync_task.apply_async((run.id,), task_id=run.task_id)
