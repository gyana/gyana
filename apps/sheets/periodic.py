from celery import shared_task

from apps.base.tasks import honeybadger_check_in

from .models import Sheet
from .tasks import run_periodic_sheet_sync

# Timeout after 10 minutes, for the new task to start. Tasks are idempotent and
# commit for each connector, so there is no loss in data and this way we avoid
# task congestion.


@shared_task(timeout=600)
def run_schedule_for_sheets():

    for sheet in Sheet.objects.needs_daily_sync().all():
        run_periodic_sheet_sync(sheet)

    honeybadger_check_in("j6IrRd")
