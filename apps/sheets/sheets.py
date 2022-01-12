import re

from django.utils.dateparse import parse_datetime

from apps.base import clients

from .models import Sheet


def get_sheets_id_from_url(url: str):
    p = re.compile(r"[-\w]{25,}")
    return res.group(0) if (res := p.search(url)) else ""


def get_metadata_from_sheet(sheet: Sheet):

    sheet_id = get_sheets_id_from_url(sheet.url)
    client = clients.sheets()
    return client.spreadsheets().get(spreadsheetId=sheet_id).execute()


def get_metadata_from_drive_file(sheet: Sheet):

    sheet_id = get_sheets_id_from_url(sheet.url)
    client = clients.drive_v2()
    return client.files().get(fileId=sheet_id, supportsAllDrives=True).execute()


def get_last_modified_from_drive_file(sheet: Sheet):

    drive_file = get_metadata_from_drive_file(sheet)
    return parse_datetime(drive_file["modifiedDate"])


def get_cell_range(sheet_name, cell_range):
    return (
        f"{sheet_name}!{cell_range}"
        if sheet_name and cell_range
        else sheet_name or cell_range
    )
