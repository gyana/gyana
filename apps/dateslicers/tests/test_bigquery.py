import datetime as dt

import ibis_bigquery
import pytest

from apps.base.tests.mock_data import TABLE
from apps.dateslicers.bigquery import slice_query
from apps.dateslicers.models import CustomChoice, DateSlicer


QUERY = "SELECT *\nFROM olympians\nWHERE {}"


@pytest.mark.parametrize(
    "date_range, expected_sql",
    [
        pytest.param(
            CustomChoice.CUSTOM,
            QUERY.format(f"`birthday` = DATE '{dt.date.today().isoformat()}'"),
            id="custom",
        )
    ],
)
def test_slice_query_ranges(date_range, expected_sql):
    date_slicer = DateSlicer(date_range=date_range)
    query = slice_query(TABLE, "birthday", date_slicer)

    assert ibis_bigquery.compile(query) == expected_sql
