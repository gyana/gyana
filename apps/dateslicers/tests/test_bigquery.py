import datetime as dt

import ibis_bigquery
import pytest

from apps.base.tests.mock_data import TABLE
from apps.dateslicers.bigquery import slice_query
from apps.dateslicers.models import CustomChoice, DateSlicer

QUERY = "SELECT *\nFROM olympians\nWHERE {}"

SASCHAS_BIRTHDAY = dt.date(1993, 7, 26)
DAVIDS_BIRTHDAY = dt.date(1992, 8, 3)


@pytest.mark.parametrize(
    "date_range,start,end, expected_sql",
    [
        pytest.param(
            CustomChoice.CUSTOM,
            SASCHAS_BIRTHDAY,
            None,
            QUERY.format(f"`birthday` > DATE '{SASCHAS_BIRTHDAY.isoformat()}'"),
            id="custom with start",
        ),
        pytest.param(
            CustomChoice.CUSTOM,
            None,
            SASCHAS_BIRTHDAY,
            QUERY.format(f"`birthday` < DATE '{SASCHAS_BIRTHDAY.isoformat()}'"),
            id="custom with end",
        ),
        pytest.param(
            CustomChoice.CUSTOM,
            DAVIDS_BIRTHDAY,
            SASCHAS_BIRTHDAY,
            QUERY.format(
                f"(`birthday` > DATE '{DAVIDS_BIRTHDAY.isoformat()}') AND\n      (`birthday` < DATE '{SASCHAS_BIRTHDAY.isoformat()}')"
            ),
            id="custom with start and end",
        ),
    ],
)
def test_slice_query_ranges(date_range, start, end, expected_sql):
    date_slicer = DateSlicer(date_range=date_range, start=start, end=end)
    query = slice_query(TABLE, "birthday", date_slicer)

    assert ibis_bigquery.compile(query) == expected_sql
