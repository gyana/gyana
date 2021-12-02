from celery import shared_task

from apps.sheets.models import Sheet
from apps.sheets.tasks import run_periodic_sheet_sync

from .models import Project


@shared_task
def run_schedule_for_project(project_id):

    project = Project.objects.get(pk=project_id)

    if not project.needs_schedule:
        project.periodic_task.delete()
        return

    for sheet in (
        Sheet.objects.filter(integration__project=project).needs_daily_sync().all()
    ):
        run_periodic_sheet_sync(sheet.id)
