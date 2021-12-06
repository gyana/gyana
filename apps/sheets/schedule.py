from apps.projects.models import Project

from .models import Sheet
from .tasks import run_sheet_sync_task


def run_scheduled_sheets(project: Project):

    for sheet in Sheet.objects.is_scheduled_in_project(project).all():
        try:
            run_sheet_sync_task(sheet.id, skip_up_to_date=True)
        except:
            # error state is already logged to database
            pass
