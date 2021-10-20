from apps.base.tasks import honeybadger_check_in
from apps.connectors.tasks import run_connector_sync
from apps.sheets.tasks import run_sheet_sync
from apps.uploads.tasks import run_upload_sync
from celery.app import shared_task

from .models import Integration

KIND_TO_SYNC_TASK = {
    Integration.Kind.CONNECTOR: run_connector_sync,
    Integration.Kind.SHEET: run_sheet_sync,
    Integration.Kind.UPLOAD: run_upload_sync,
}

PENDING_DELETE_AFTER_DAYS = 7


@shared_task
def delete_outdated_pending_integrations():
    # will automatically delete associated fivetran and bigquery entities
    Integration.objects.pending_should_be_deleted().delete()

    honeybadger_check_in("LoI4LK")
