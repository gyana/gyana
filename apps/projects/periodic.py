from uuid import uuid4

from celery import shared_task
from django.utils import timezone

from apps.base.tasks import honeybadger_check_in
from apps.projects.models import Project
from apps.runs.models import GraphRun

from . import tasks
from .models import Project

# Retry every 10 minutes for next 6 hours, this will continue to try until
# the incremental connector resyncs are completed.
RETRY_COUNTDOWN = 60 * 10
MAX_RETRIES = 3600 / RETRY_COUNTDOWN * 24


@shared_task(bind=True)
def run_schedule_for_project(self, project_id: int):

    project = Project.objects.get(pk=project_id)

    project.update_schedule()

    # skip workflow if nothing to run
    if project.periodic_task is None:
        return

    # todo: We need to keep retrying until the connectors either fail or succeeded
    # if {{ connectors_not_ready }}:
    #     self.retry(countdown=RETRY_COUNTDOWN, max_retries=MAX_RETRIES)

    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=GraphRun.State.RUNNING,
        started_at=timezone.now(),
    )
    tasks.run_project_task(graph_run.id, scheduled_only=True)

    honeybadger_check_in("j6IrRd")
