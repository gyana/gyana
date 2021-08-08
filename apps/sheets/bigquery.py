import re

from apps.base.clients import sheets_client
from google.cloud import bigquery


def create_external_sheets_config(url: str, cell_range=None) -> bigquery.ExternalConfig:
    """
    Constructs a BQ external config.

    For a Google Sheets integration `url` is required and `cell_range` is optional
    """

    # https://cloud.google.com/bigquery/external-data-drive#python
    external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
    external_config.source_uris = [url]
    # Only include cell range when it exists
    if cell_range:
        external_config.options.range = cell_range

    external_config.autodetect = True

    return external_config


def get_sheets_id_from_url(url):
    p = re.compile(r"[-\w]{25,}")
    return res.group(0) if (res := p.search(url)) else ""


def get_metadata_from_sheet(self):

    sheet_id = get_sheets_id_from_url(self.url)
    client = sheets_client()
    return client.spreadsheets().get(spreadsheetId=sheet_id).execute()


def start_sheets_sync(self):
    from apps.sheets.tasks import run_sheets_sync

    result = run_sheets_sync.delay(self.id)
    self.sheet.external_table_sync_task_id = result.task_id

    self.sheet.save()
