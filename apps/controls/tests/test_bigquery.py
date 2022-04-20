import datetime as dt

import ibis_bigquery
import pytest
from dateutil.relativedelta import relativedelta

from apps.base.tests.mock_data import TABLE
from apps.controls.bigquery import get_quarter, slice_query
from apps.controls.models import Control, CustomChoice, DateRange

QUERY = "SELECT *\nFROM olympians\nWHERE {}"

SASCHAS_BIRTHDAY = dt.date(1993, 7, 26)
DAVIDS_BIRTHDAY = dt.date(1992, 8, 3)


@pytest.mark.parametrize(
    "date_range, start, end, expected_sql",
    [
        pytest.param(
            CustomChoice.CUSTOM,
            SASCHAS_BIRTHDAY,
            None,
            QUERY.format(f"`birthday` >= DATE '{SASCHAS_BIRTHDAY.isoformat()}'"),
            id="custom with start",
        ),
        pytest.param(
            CustomChoice.CUSTOM,
            None,
            SASCHAS_BIRTHDAY,
            QUERY.format(f"`birthday` <= DATE '{SASCHAS_BIRTHDAY.isoformat()}'"),
            id="custom with end",
        ),
        pytest.param(
            CustomChoice.CUSTOM,
            DAVIDS_BIRTHDAY,
            SASCHAS_BIRTHDAY,
            QUERY.format(
                f"(`birthday` >= DATE '{DAVIDS_BIRTHDAY.isoformat()}') AND\n      (`birthday` <= DATE '{SASCHAS_BIRTHDAY.isoformat()}')"
            ),
            id="custom with start and end",
        ),
    ],
)
def test_slice_query_custom_range(date_range, start, end, expected_sql):
    control = Control(date_range=date_range, start=start, end=end)
    query = slice_query(TABLE, "birthday", control, False)

    assert ibis_bigquery.compile(query) == expected_sql


TODAY = dt.date.today()


def create_previous_last_n_days(date_range, days):
    return pytest.param(
        date_range,
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY - dt.timedelta(days=2*days)).isoformat()}' AND DATE '{(TODAY-dt.timedelta(days=days)).isoformat()}'"
        ),
        id=f"Date on last {days}",
    )


@pytest.mark.parametrize(
    "date_range, expected_sql",
    [
        pytest.param(
            DateRange.TODAY,
            QUERY.format(
                f"`birthday` = DATE '{(TODAY - dt.timedelta(days=1)).isoformat()}'"
            ),
            id="today",
        ),
        pytest.param(
            DateRange.TOMORROW,
            QUERY.format(f"`birthday` = DATE '{TODAY.isoformat()}'"),
            id="tomorrow",
        ),
        pytest.param(
            DateRange.YESTERDAY,
            QUERY.format(
                f"`birthday` = DATE '{(TODAY-dt.timedelta(days=2)).isoformat()}'"
            ),
            id="yesterday",
        ),
        pytest.param(
            DateRange.ONEWEEKAGO,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY - dt.timedelta(days=14)).isoformat()}' AND DATE '{(TODAY - dt.timedelta(days=7)).isoformat()}'"
            ),
            id="oneweekago",
        ),
        pytest.param(
            DateRange.ONEMONTHAGO,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=2)).isoformat()}' AND DATE '{(TODAY - relativedelta(months=1)).isoformat()}'"
            ),
            id="onemonthago",
        ),
        pytest.param(
            DateRange.ONEYEARAGO,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(years=2)).isoformat()}' AND DATE '{(TODAY - relativedelta(years=1)).isoformat()}'"
            ),
            id="oneyearago",
        ),
        pytest.param(
            DateRange.THIS_WEEK,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY - dt.timedelta(days=7)).year}) AND\n      (EXTRACT(ISOWEEK from `birthday`) = {(TODAY - dt.timedelta(days=7)).isocalendar()[1]})"
            ),
            id="thisweek",
        ),
        pytest.param(
            DateRange.THIS_WEEK_UP_TO_DATE,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY - dt.timedelta(days=7+TODAY.weekday())).isoformat()}' AND DATE '{(TODAY - dt.timedelta(days=7)).isoformat()}'"
            ),
            id="thisweekuptodate",
        ),
        pytest.param(
            DateRange.LAST_WEEK,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY - dt.timedelta(days=14)).year}) AND\n      (EXTRACT(ISOWEEK from `birthday`) = {(TODAY - dt.timedelta(days=14)).isocalendar()[1]})"
            ),
            id="lastweek",
        ),
        create_previous_last_n_days(DateRange.LAST_7, 7),
        create_previous_last_n_days(DateRange.LAST_14, 14),
        create_previous_last_n_days(DateRange.LAST_28, 28),
        create_previous_last_n_days(DateRange.LAST_30, 30),
        create_previous_last_n_days(DateRange.LAST_90, 90),
        create_previous_last_n_days(DateRange.LAST_180, 180),
        pytest.param(
            DateRange.THIS_MONTH,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY - relativedelta(months=1)).year}) AND\n      (EXTRACT(month from `birthday`) = {(TODAY - relativedelta(months=1)).month})"
            ),
            id="thismonth",
        ),
        pytest.param(
            DateRange.THIS_MONTH_UP_TO_DATE,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=1)).replace(day=1).isoformat()}' AND DATE '{(TODAY - relativedelta(months=1)).isoformat()}'"
            ),
            id="thismonthuptodate",
        ),
        pytest.param(
            DateRange.LAST_MONTH,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY - relativedelta(months=2)).year}) AND\n      (EXTRACT(month from `birthday`) = {(TODAY - relativedelta(months=2)).month})"
            ),
            id="lastmonth",
        ),
        pytest.param(
            DateRange.THIS_YEAR,
            QUERY.format(
                f"EXTRACT(year from `birthday`) = { (TODAY -relativedelta(years=1)).year }"
            ),
            id="thisyear",
        ),
        pytest.param(
            DateRange.THIS_YEAR_UP_TO_DATE,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY -relativedelta(years=1)).year }) AND\n      (`birthday` <= DATE '{(TODAY -relativedelta(years=1)).isoformat()}')"
            ),
            id="thisyearuptodate",
        ),
        pytest.param(
            DateRange.LAST_YEAR,
            QUERY.format(
                f"EXTRACT(year from `birthday`) = {(TODAY -relativedelta(years=2)).year }"
            ),
            id="lastyear",
        ),
        pytest.param(
            DateRange.THIS_QUARTER,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY-relativedelta(months=3)).year}) AND\n      (EXTRACT(quarter from `birthday`) = {get_quarter((TODAY-relativedelta(months=3)))})"
            ),
            id="thisquarter",
        ),
        pytest.param(
            DateRange.THIS_QUARTER_UP_TO_DATE,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{dt.date((TODAY-relativedelta(months=3)).year, (get_quarter(TODAY-relativedelta(months=3))-1)*3+1, 1).isoformat()}' AND DATE '{(TODAY-relativedelta(months=3)).isoformat()}'"
            ),
            id="thisquarteruptodate",
        ),
        pytest.param(
            DateRange.LAST_QUARTER,
            QUERY.format(
                f"(EXTRACT(year from `birthday`) = {(TODAY-relativedelta(months=6)).year}) AND\n      (EXTRACT(quarter from `birthday`) = {get_quarter(TODAY-relativedelta(months=6))})"
            ),
            id="lastquarter",
        ),
        pytest.param(
            DateRange.LAST_12_MONTH,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=24)).isoformat()}' AND DATE '{(TODAY - relativedelta(months=12)).isoformat()}'"
            ),
            id="last12month",
        ),
        pytest.param(
            DateRange.LAST_FULL_12_MONTH,
            QUERY.format(
                f"`birthday` BETWEEN DATE '{(TODAY.replace(day=1) - relativedelta(months=24)).isoformat()}' AND DATE '{(TODAY - relativedelta(months=12)).isoformat()}'"
            ),
            id="lastfull12month",
        ),
    ],
)
def test_previous_function(date_range, expected_sql):
    control = Control(date_range=date_range)
    query = slice_query(TABLE, "birthday", control, True)

    assert ibis_bigquery.compile(query) == expected_sql
