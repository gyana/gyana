from celery import shared_task

from apps.base.tasks import honeybadger_check_in
from apps.sheets.models import Sheet
from apps.sheets.tasks import run_sheet_sync_task

from .models import Project


@shared_task
def run_schedule_for_project(project_id):

    project = Project.objects.get(pk=project_id)

    # cleanup periodic task for projects with no scheduled items
    if not project.needs_schedule:
        project.update_schedule()
        return

    for sheet in Sheet.objects.is_scheduled_in_project(project).all():
        run_sheet_sync_task(sheet.id, skip_up_to_date=True)

    honeybadger_check_in("j6IrRd")
