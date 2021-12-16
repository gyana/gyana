from apps.connectors.sync import start_connector_sync
from apps.customapis.tasks import run_customapi_sync
from apps.sheets.tasks import run_sheet_sync
from apps.uploads.tasks import run_upload_sync
from apps.users.models import CustomUser

from .models import Integration


def run_integration(kind: Integration.Kind, entity, user: CustomUser):
    return {
        Integration.Kind.CONNECTOR: start_connector_sync,
        Integration.Kind.CUSTOMAPI: run_customapi_sync,
        Integration.Kind.SHEET: run_sheet_sync,
        Integration.Kind.UPLOAD: run_upload_sync,
    }[kind](entity, user)
