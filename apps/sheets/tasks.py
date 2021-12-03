from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.base.time import catchtime
from apps.integrations.emails import send_integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table

from .bigquery import import_table_from_sheet
from .models import Sheet


@shared_task(bind=True)
def run_sheet_sync_task(self, sheet_id, skip_up_to_date=False):
    sheet = get_object_or_404(Sheet, pk=sheet_id)
    integration = sheet.integration

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    try:

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
                    import_table_from_sheet(table=table, sheet=sheet)

                table.sync_updates_from_bigquery()
                sheet.drive_file_last_modified_at_sync = sheet.drive_modified_date

            sheet.succeeded_at = timezone.now()
            sheet.save()

            integration.state = Integration.State.DONE
            integration.save()

            sheet.integration.project.update_schedule()

    except Exception as e:
        sheet.failed_at = timezone.now()
        sheet.save()

        integration.state = Integration.State.ERROR
        integration.save()
        raise e

    if created:
        send_integration_ready_email(integration, int(get_time_to_sync()))

    return integration.id


def run_sheet_sync(sheet: Sheet):

    sheet.integration.state = Integration.State.LOAD
    sheet.integration.save()

    result = run_sheet_sync_task.delay(sheet.id)
    sheet.refresh_from_db()  # required for tests
    sheet.sync_task_id = result.task_id
    sheet.sync_started = timezone.now()
    sheet.save()
