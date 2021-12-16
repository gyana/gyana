from datetime import timedelta
from uuid import uuid4

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from apps.base.tasks import honeybadger_check_in
from apps.connectors.models import Connector
from apps.projects.models import Project
from apps.projects.schedule import get_next_daily_sync_in_utc_from_project
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

    # skip and delete periodic tasks if nothing to schedule
    if project.periodic_task is None:
        return

    current_schedule = get_next_daily_sync_in_utc_from_project(project) - timedelta(
        days=1
    )

    # wait until all the connectors we expect to sync have completed for today
    connectors_not_ready = (
        Connector.objects.filter(
            setup_state=Connector.SetupState.CONNECTED,
            paused=False,
            integration__ready=True,
        )
        .exclude(
            Q(succeeded_at__gt=current_schedule) | Q(failed_at__gt=current_schedule)
        )
        .exists()
    )

    if connectors_not_ready:
        self.retry(countdown=RETRY_COUNTDOWN, max_retries=MAX_RETRIES)

    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=GraphRun.State.RUNNING,
        started_at=timezone.now(),
    )
    tasks.run_project_task(graph_run.id, scheduled_only=True)

    honeybadger_check_in("j6IrRd")
