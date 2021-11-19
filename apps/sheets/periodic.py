from celery import shared_task

from apps.base.tasks import honeybadger_check_in

from .models import Sheet
from .tasks import run_periodic_sheet_sync


@shared_task
def run_schedule_for_sheets():

    for sheet in Sheet.objects.needs_daily_sync().all():
        run_periodic_sheet_sync(sheet)

    # honeybadger_check_in("TODO")
