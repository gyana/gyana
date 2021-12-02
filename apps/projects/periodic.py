from celery import shared_task

from apps.base.tasks import honeybadger_check_in
from apps.sheets.models import Sheet
from apps.sheets.tasks import run_sheet_sync_task

from .models import Project


@shared_task
def run_schedule_for_project(project_id):

    project = Project.objects.get(pk=project_id)

    if not project.needs_schedule:
        project.periodic_task.delete()
        return

    for sheet in (
        Sheet.objects.filter(integration__project=project).scheduled_for_today().all()
    ):
        run_sheet_sync_task(sheet.id, skip_up_to_date=True)

    honeybadger_check_in("j6IrRd")
