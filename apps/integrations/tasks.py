from apps.customapis import tasks as customapi_tasks
from apps.sheets import tasks as sheet_tasks
from apps.uploads.tasks import run_upload_sync
from apps.users.models import CustomUser

from .models import Integration


def run_integration_task(kind: Integration.Kind, run_id: str):
    # todo: in future, we have the option to skip the sync for a google sheet if
    # it is already up to date
    return {
        Integration.Kind.CUSTOMAPI: customapi_tasks.run_customapi_sync_task,
        Integration.Kind.SHEET: sheet_tasks.run_sheet_sync_task,
    }[kind](run_id)


def run_integration(kind: Integration.Kind, entity, user: CustomUser):
    return {
        Integration.Kind.CUSTOMAPI: customapi_tasks.run_customapi_sync,
        Integration.Kind.SHEET: sheet_tasks.run_sheet_sync,
        Integration.Kind.UPLOAD: run_upload_sync,
    }[kind](entity, user)
