from graphlib import CycleError

from celery import shared_task

from apps.base.tasks import honeybadger_check_in
from apps.projects.models import Project
from apps.sheets.tasks import run_scheduled_sheets
from apps.workflows.bigquery import run_scheduled_workflows

# Retry every 10 minutes for next 12 hours, this will continue to try until
# the incremental connector resyncs are completed.
RETRY_COUNTDOWN = 60 * 10
MAX_RETRIES = 3600 / RETRY_COUNTDOWN * 12


@shared_task(bind=True)
def run_schedule_for_project(self, project_id: int):

    project = Project.objects.get(pk=project_id)

    project.update_schedule()

    # skip workflow if nothing to run
    if project.schedule.periodic_task is None:
        return

    run_scheduled_sheets(project)
    try:
        run_scheduled_workflows(project)
    except CycleError:
        # todo: add an error to the schedule to track "is_circular"
        pass

    # todo: compute retry criteria here
    retry = False

    # We need to keep retrying until the connectors either fail or succeeded
    if retry:
        self.retry(countdown=RETRY_COUNTDOWN, max_retries=MAX_RETRIES)

    honeybadger_check_in("j6IrRd")
