import json
from graphlib import CycleError

from celery import shared_task
from celery_progress.backend import ProgressRecorder

from apps.base.tasks import honeybadger_check_in
from apps.schedules.models import Schedule
from apps.sheets.schedule import run_scheduled_sheets
from apps.workflows.schedule import run_scheduled_workflows

# Retry every 10 minutes for next 12 hours, this will continue to try until
# the incremental connector resyncs are completed.
RETRY_COUNTDOWN = 60 * 10
MAX_RETRIES = 3600 / RETRY_COUNTDOWN * 12


@shared_task(bind=True)
def run_schedule(self, schedule_id: int):

    progress_recorder = ProgressRecorder(self)
    run_info = {}

    schedule = Schedule.objects.get(pk=schedule_id)

    schedule.update_schedule()

    # skip workflow if nothing to run
    if not schedule.periodic_task.enabled:
        return

    for schedule_node_id, run_status in run_scheduled_sheets(schedule.project):
        run_info[schedule_node_id] = run_status
        progress_recorder.set_progress(0, 0, description=json.dumps(run_info))
    try:
        for schedule_node_id, run_status in run_scheduled_workflows(schedule.project):
            run_info[schedule_node_id] = run_status
            progress_recorder.set_progress(0, 0, description=json.dumps(run_info))
    except CycleError:
        # todo: add an error to the schedule to track "is_circular"
        pass

    # We need to keep retrying until the connectors either fail or succeeded
    if not schedule.latest_schedule_is_complete:
        self.retry(countdown=RETRY_COUNTDOWN, max_retries=MAX_RETRIES)

    honeybadger_check_in("j6IrRd")
