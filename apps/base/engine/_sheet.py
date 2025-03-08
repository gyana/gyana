from functools import lru_cache
from typing import TYPE_CHECKING

import gspread
import pandas as pd

from .credentials import get_credentials

if TYPE_CHECKING:
    from apps.sheets.models import Sheet


@lru_cache
def google_client():
    creds, _ = get_credentials()
    return gspread.authorize(creds)


def create_dataframe_from_sheet(sheet: "Sheet"):
    gc = google_client()
    spreadsheet = gc.open_by_url(sheet.url)

    if sheet.sheet_name:
        worksheet = spreadsheet.worksheet(sheet.sheet_name)
    else:
        worksheet = spreadsheet.get_worksheet(0)

    if sheet.cell_range:
        data = worksheet.get(sheet.cell_range)
        if len(data) == 0:
            raise ValueError("No columns found in the schema.")
        return pd.DataFrame(data[1:], columns=data[0])

    return pd.DataFrame(worksheet.get_all_records())
