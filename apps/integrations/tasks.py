from apps.connectors.tasks import run_connector_sync
from apps.sheets.tasks import run_sheet_sync
from apps.uploads.tasks import run_upload_sync

from .models import Integration

KIND_TO_SYNC_TASK = {
    Integration.Kind.CONNECTOR: run_connector_sync,
    Integration.Kind.SHEET: run_sheet_sync,
    Integration.Kind.UPLOAD: run_upload_sync,
}
