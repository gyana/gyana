from celery import shared_task

from apps.sheets.models import Sheet
from apps.sheets.tasks import run_sheet_sync_task


@shared_task
def run_schedule_for_project():

    for sheet in Sheet.objects.needs_daily_sync().all():
        run_sheet_sync_task(sheet.id)
