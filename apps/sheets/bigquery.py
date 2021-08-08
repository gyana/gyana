import re

from apps.base.clients import (
    DATASET_ID,
    bigquery_client,
    drive_v2_client,
    sheets_client,
)
from apps.tables.models import Table
from django.utils.dateparse import parse_datetime
from google.cloud import bigquery
from google.cloud.bigquery.job.query import QueryJob

from .models import Sheet


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


def import_table_from_sheet(table: Table, sheet: Sheet) -> QueryJob:
    """
    Copy Google Sheet to BigQuery table via temporary external table.

    Having data in a bq table rather than an external source makes using it much faster.

    https://cloud.google.com/bigquery/docs/tables-intro
    """

    external_config = create_external_sheets_config(sheet.url, sheet.cell_range)

    client = bigquery_client()

    job_config = bigquery.QueryJobConfig(
        table_definitions={table.bq_external_table_id: external_config}
    )

    query_job = client.query(
        f"CREATE OR REPLACE TABLE {DATASET_ID}.{table.bq_table} AS SELECT * FROM {table.bq_external_table_id}",
        job_config=job_config,
    )

    return query_job


def get_sheets_id_from_url(url: str):
    p = re.compile(r"[-\w]{25,}")
    return res.group(0) if (res := p.search(url)) else ""


def get_metadata_from_sheet(sheet: Sheet):

    sheet_id = get_sheets_id_from_url(sheet.url)
    client = sheets_client()
    return client.spreadsheets().get(spreadsheetId=sheet_id).execute()


def get_metadata_from_drive_file(sheet: Sheet):

    sheet_id = get_sheets_id_from_url(sheet.url)
    client = drive_v2_client()
    return client.files().get(fileId=sheet_id).execute()


def get_last_modified_from_drive_file(sheet: Sheet):

    drive_file = get_metadata_from_drive_file(sheet)

    return parse_datetime(drive_file["modifiedDate"])
