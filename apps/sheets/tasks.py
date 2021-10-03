from datetime import datetime

import analytics
from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.base.time import catchtime
from apps.integrations.emails import integration_ready_email
from apps.integrations.models import Integration
from apps.tables.models import Table
from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .bigquery import get_last_modified_from_drive_file, import_table_from_sheet
from .models import Sheet


@shared_task(bind=True)
def run_sheet_sync_task(self, sheet_id):
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

            sheet.drive_file_last_modified = get_last_modified_from_drive_file(sheet)

            with catchtime() as get_time_to_sync:
                import_table_from_sheet(table=table, sheet=sheet)

            table.num_rows = table.bq_obj.num_rows
            table.data_updated = datetime.now()
            table.save()

            sheet.last_synced = datetime.now()
            sheet.save()

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
                "time_to_sync": int(get_time_to_sync()),
            },
        )

    return integration.id


def run_sheet_sync(sheet: Sheet):

    sheet.integration.state = Integration.State.LOAD
    sheet.integration.save()

    result = run_sheet_sync_task.delay(sheet.id)
    sheet.sync_task_id = result.task_id
    sheet.sync_started = timezone.now()
    sheet.save()
