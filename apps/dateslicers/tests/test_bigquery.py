import datetime as dt

import pytest

from apps.base.tests.mock_data import TABLE
from apps.dateslicers.bigquery import slice_query
from apps.dateslicers.models import DateSlicer

Range = DateSlicer.Range


QUERY = "SELECT *\nFROM olympians\nWHERE {}"


@pytest.mark.parametrize(
    "date_range, expected_sql",
    [
        pytest.param(
            Range.TODAY,
            QUERY.format(f"`birthday` = DATE '{dt.date.today().isoformat()}'"),
            id="today",
        )
    ],
)
def test_slice_query_ranges(date_range, expected_sql):
    date_slicer = DateSlicer(date_range=date_range)
    query = slice_query(TABLE, "birthday", date_slicer)

    assert query.compile() == expected_sql
