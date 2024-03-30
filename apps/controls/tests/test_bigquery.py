import datetime as dt

import pytest
from dateutil.relativedelta import relativedelta
from ibis import bigquery

from apps.controls.engine import get_quarter, slice_query
from apps.controls.models import Control, CustomChoice, DateRange

QUERY = "SELECT\n  t0.*\nFROM `project.dataset`.table AS t0\nWHERE\n  {}"

SASCHAS_BIRTHDAY = dt.date(1993, 7, 26)
DAVIDS_BIRTHDAY = dt.date(1992, 8, 3)


@pytest.mark.parametrize(
    "date_range, start, end, expected_sql",
    [
        pytest.param(
            CustomChoice.CUSTOM,
            SASCHAS_BIRTHDAY,
            None,
            QUERY.format(
                f"t0.`birthday` >= CAST('{SASCHAS_BIRTHDAY.isoformat()}' AS DATE)"
            ),
            id="custom with start",
        ),
        pytest.param(
            CustomChoice.CUSTOM,
            None,
            SASCHAS_BIRTHDAY,
            QUERY.format(
                f"t0.`birthday` <= CAST('{SASCHAS_BIRTHDAY.isoformat()}' AS DATE)"
            ),
            id="custom with end",
        ),
        pytest.param(
            CustomChoice.CUSTOM,
            DAVIDS_BIRTHDAY,
            SASCHAS_BIRTHDAY,
            QUERY.format(
                f"(\n    t0.`birthday` >= CAST('{DAVIDS_BIRTHDAY.isoformat()}' AS DATE)\n  )\n  AND (\n    t0.`birthday` <= CAST('{SASCHAS_BIRTHDAY.isoformat()}' AS DATE)\n  )"
            ),
            id="custom with start and end",
        ),
    ],
)
def test_slice_query_custom_range(date_range, start, end, expected_sql, engine):
    control = Control(date_range=date_range, start=start, end=end)
    query = slice_query(engine.data, "birthday", control, False)

    assert bigquery.compile(query) == expected_sql


TODAY = dt.date.today()


def create_previous_last_n_days(date_range, days):
    return pytest.param(
        date_range,
        QUERY.format(
            f"t0.`birthday` BETWEEN CAST('{(TODAY - dt.timedelta(days=2*days)).isoformat()}' AS DATE) AND CAST('{(TODAY-dt.timedelta(days=days)).isoformat()}' AS DATE)"
        ),
        id=f"Date on last {days}",
    )


@pytest.mark.parametrize(
    "date_range, expected_sql",
    [
        pytest.param(
            DateRange.TODAY,
            QUERY.format(
                f"t0.`birthday` = CAST('{(TODAY - dt.timedelta(days=1)).isoformat()}' AS DATE)"
            ),
            id="today",
        ),
        pytest.param(
            DateRange.TOMORROW,
            QUERY.format(f"t0.`birthday` = CAST('{TODAY.isoformat()}' AS DATE)"),
            id="tomorrow",
        ),
        pytest.param(
            DateRange.YESTERDAY,
            QUERY.format(
                f"t0.`birthday` = CAST('{(TODAY-dt.timedelta(days=2)).isoformat()}' AS DATE)"
            ),
            id="yesterday",
        ),
        pytest.param(
            DateRange.ONEWEEKAGO,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY - dt.timedelta(days=14)).isoformat()}' AS DATE) AND CAST('{(TODAY - dt.timedelta(days=7)).isoformat()}' AS DATE)"
            ),
            id="oneweekago",
        ),
        pytest.param(
            DateRange.ONEMONTHAGO,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY - relativedelta(months=2)).isoformat()}' AS DATE) AND CAST('{(TODAY - relativedelta(months=1)).isoformat()}' AS DATE)"
            ),
            id="onemonthago",
        ),
        pytest.param(
            DateRange.ONEYEARAGO,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY - relativedelta(years=2)).isoformat()}' AS DATE) AND CAST('{(TODAY - relativedelta(years=1)).isoformat()}' AS DATE)"
            ),
            id="oneyearago",
        ),
        pytest.param(
            DateRange.THIS_WEEK,
            QUERY.format(
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY - dt.timedelta(days=7)).year}\n  )\n  AND (\n    EXTRACT(ISOWEEK FROM t0.`birthday`) = {(TODAY - dt.timedelta(days=7)).isocalendar()[1]}\n  )"
            ),
            id="thisweek",
        ),
        pytest.param(
            DateRange.THIS_WEEK_UP_TO_DATE,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY - dt.timedelta(days=7+TODAY.weekday())).isoformat()}' AS DATE) AND CAST('{(TODAY - dt.timedelta(days=7)).isoformat()}' AS DATE)"
            ),
            id="thisweekuptodate",
        ),
        pytest.param(
            DateRange.LAST_WEEK,
            QUERY.format(
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY - dt.timedelta(days=14)).year}\n  )\n  AND (\n    EXTRACT(ISOWEEK FROM t0.`birthday`) = {(TODAY - dt.timedelta(days=14)).isocalendar()[1]}\n  )"
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
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY - relativedelta(months=1)).year}\n  )\n  AND (\n    EXTRACT(month FROM t0.`birthday`) = {(TODAY - relativedelta(months=1)).month}\n  )"
            ),
            id="thismonth",
        ),
        pytest.param(
            DateRange.THIS_MONTH_UP_TO_DATE,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY - relativedelta(months=1)).replace(day=1).isoformat()}' AS DATE) AND CAST('{(TODAY - relativedelta(months=1)).isoformat()}' AS DATE)"
            ),
            id="thismonthuptodate",
        ),
        pytest.param(
            DateRange.LAST_MONTH,
            QUERY.format(
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY - relativedelta(months=2)).year}\n  )\n  AND (\n    EXTRACT(month FROM t0.`birthday`) = {(TODAY - relativedelta(months=2)).month}\n  )"
            ),
            id="lastmonth",
        ),
        pytest.param(
            DateRange.THIS_YEAR,
            QUERY.format(
                f"EXTRACT(year FROM t0.`birthday`) = { (TODAY -relativedelta(years=1)).year }"
            ),
            id="thisyear",
        ),
        pytest.param(
            DateRange.THIS_YEAR_UP_TO_DATE,
            QUERY.format(
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY -relativedelta(years=1)).year }\n  )\n  AND (\n    t0.`birthday` <= CAST('{(TODAY -relativedelta(years=1)).isoformat()}' AS DATE)\n  )"
            ),
            id="thisyearuptodate",
        ),
        pytest.param(
            DateRange.LAST_YEAR,
            QUERY.format(
                f"EXTRACT(year FROM t0.`birthday`) = {(TODAY -relativedelta(years=2)).year }"
            ),
            id="lastyear",
        ),
        pytest.param(
            DateRange.THIS_QUARTER,
            QUERY.format(
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY-relativedelta(months=3)).year}\n  )\n  AND (\n    EXTRACT(quarter FROM t0.`birthday`) = {get_quarter((TODAY-relativedelta(months=3)))}\n  )"
            ),
            id="thisquarter",
        ),
        pytest.param(
            DateRange.THIS_QUARTER_UP_TO_DATE,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{dt.date((TODAY-relativedelta(months=3)).year, (get_quarter(TODAY-relativedelta(months=3))-1)*3+1, 1).isoformat()}' AS DATE) AND CAST('{(TODAY-relativedelta(months=3)).isoformat()}' AS DATE)"
            ),
            id="thisquarteruptodate",
        ),
        pytest.param(
            DateRange.LAST_QUARTER,
            QUERY.format(
                f"(\n    EXTRACT(year FROM t0.`birthday`) = {(TODAY-relativedelta(months=6)).year}\n  )\n  AND (\n    EXTRACT(quarter FROM t0.`birthday`) = {get_quarter(TODAY-relativedelta(months=6))}\n  )"
            ),
            id="lastquarter",
        ),
        pytest.param(
            DateRange.LAST_12_MONTH,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY - relativedelta(months=24)).isoformat()}' AS DATE) AND CAST('{(TODAY - relativedelta(months=12)).isoformat()}' AS DATE)"
            ),
            id="last12month",
        ),
        pytest.param(
            DateRange.LAST_FULL_12_MONTH,
            QUERY.format(
                f"t0.`birthday` BETWEEN CAST('{(TODAY.replace(day=1) - relativedelta(months=24)).isoformat()}' AS DATE) AND CAST('{(TODAY - relativedelta(months=12)).isoformat()}' AS DATE)"
            ),
            id="lastfull12month",
        ),
    ],
)
def test_previous_function(date_range, expected_sql, engine):
    control = Control(date_range=date_range)
    query = slice_query(engine.data, "birthday", control, True)

    assert bigquery.compile(query) == expected_sql
