from uuid import uuid4

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.base.clients import get_engine
from apps.base.core.utils import catchtime
from apps.integrations.emails import send_integration_ready_email
from apps.runs.models import JobRun
from apps.tables.models import Table
from apps.users.models import CustomUser

from .models import Sheet


@shared_task(bind=True)
def run_sheet_sync_task(self, run_id, skip_up_to_date=False):
    run = JobRun.objects.get(pk=run_id)
    integration = run.integration
    sheet = integration.sheet

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    with transaction.atomic():
        table, created = Table.objects.get_or_create(
            integration=integration,
            source=Table.Source.INTEGRATION,
            bq_table=sheet.table_id,
            bq_dataset=integration.project.team.tables_dataset_id,
            project=integration.project,
        )

        sheet.sync_updates_from_drive()

        if not (sheet.up_to_date_with_drive and skip_up_to_date):
            with catchtime() as get_time_to_sync:
                get_engine().import_table_from_sheet(table=table, sheet=sheet)

            table.sync_metadata_from_source()
            sheet.drive_file_last_modified_at_sync = sheet.drive_modified_date
            sheet.save()

    if created:
        send_integration_ready_email(integration, int(get_time_to_sync()))

    return integration.id


def run_sheet_sync(sheet: Sheet, user: CustomUser):
    run = JobRun.objects.create(
        source=JobRun.Source.INTEGRATION,
        integration=sheet.integration,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_sheet_sync_task.apply_async((run.id,), task_id=str(run.task_id))
