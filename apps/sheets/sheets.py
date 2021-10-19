import re

from apps.base.clients import drive_v2_client, sheets_client
from django.utils.dateparse import parse_datetime

from .models import Sheet


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
