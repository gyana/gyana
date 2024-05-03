import datetime as dt

import pytest
from dateutil.relativedelta import relativedelta

from apps.controls.engine import get_quarter, slice_query
from apps.controls.models import Control, CustomChoice, DateRange

SASCHAS_BIRTHDAY = dt.date(1993, 7, 26)
DAVIDS_BIRTHDAY = dt.date(1992, 8, 3)


@pytest.mark.parametrize(
    "start, end",
    [
        pytest.param(
            SASCHAS_BIRTHDAY,
            None,
            id="custom with start",
        ),
        pytest.param(
            None,
            SASCHAS_BIRTHDAY,
            id="custom with end",
        ),
        pytest.param(
            DAVIDS_BIRTHDAY,
            SASCHAS_BIRTHDAY,
            id="custom with start and end",
        ),
    ],
)
def test_custom_range(start, end, engine):
    control = Control(date_range=CustomChoice.CUSTOM, start=start, end=end)
    query = slice_query(engine.data, "birthday", control, False)
    expected = engine.data
    if start:
        expected = expected[expected.birthday >= start]
    if end:
        expected = expected[expected.birthday <= end]

    assert query.equals(expected)


TODAY = dt.date.today()


@pytest.mark.parametrize("previous", [False, True], ids=["current", "previous"])
@pytest.mark.parametrize(
    "date_range, date",
    [
        pytest.param(DateRange.TODAY, TODAY, id="today"),
        pytest.param(DateRange.TOMORROW, TODAY + dt.timedelta(days=1), id="tomorrow"),
        pytest.param(DateRange.YESTERDAY, TODAY - dt.timedelta(days=1), id="yesterday"),
    ],
)
def test_equals_date(engine, date_range, date, previous):
    control = Control(date_range=date_range)
    date = date - dt.timedelta(days=1) if previous else date
    query = slice_query(engine.data, "birthday", control, previous)
    assert query.equals(engine.data[engine.data.birthday == date])


def between_params(date_range, timedelta):
    return pytest.param(
        date_range,
        timedelta,
        id=date_range.label,
    )


@pytest.mark.parametrize("previous", [False, True], ids=["current", "previous"])
@pytest.mark.parametrize(
    "date_range, timedelta",
    [
        between_params(DateRange.ONEWEEKAGO, dt.timedelta(days=7)),
        between_params(DateRange.ONEMONTHAGO, relativedelta(months=1)),
        between_params(DateRange.ONEYEARAGO, relativedelta(years=1)),
        between_params(DateRange.LAST_7, dt.timedelta(days=7)),
        between_params(DateRange.LAST_14, dt.timedelta(days=14)),
        between_params(DateRange.LAST_28, dt.timedelta(days=28)),
        between_params(DateRange.LAST_30, dt.timedelta(days=30)),
        between_params(DateRange.LAST_90, dt.timedelta(days=90)),
        between_params(DateRange.LAST_180, dt.timedelta(days=180)),
        between_params(DateRange.LAST_12_MONTH, relativedelta(months=12)),
    ],
)
def test_between_dates(engine, date_range, timedelta, previous):
    control = Control(date_range=date_range)
    query = slice_query(engine.data, "birthday", control, previous)
    start = TODAY - 2 * timedelta if previous else TODAY - timedelta
    end = TODAY - timedelta if previous else TODAY
    expected = engine.data[engine.data.birthday.between(start, end)]

    assert query.equals(expected)


def range_param(date_range, timedelta, extract, second_part, previous_timedelta=None):
    previous_timedelta = previous_timedelta or 2 * timedelta
    return pytest.param(
        date_range,
        timedelta,
        previous_timedelta,
        extract,
        second_part,
        id=date_range.label,
    )


@pytest.mark.parametrize("previous", [False, True], ids=["current", "previous"])
@pytest.mark.parametrize(
    "date_range, timedelta, previous_timedelta, extract, second_part",
    [
        range_param(
            DateRange.THIS_WEEK,
            None,
            "week_of_year",
            lambda date: date.isocalendar()[1],
            dt.timedelta(days=7),
        ),
        range_param(
            DateRange.LAST_WEEK,
            dt.timedelta(days=7),
            "week_of_year",
            lambda date: date.isocalendar()[1],
        ),
        range_param(
            DateRange.THIS_MONTH,
            None,
            "month",
            lambda date: date.month,
            relativedelta(months=1),
        ),
        range_param(
            DateRange.LAST_MONTH,
            relativedelta(months=1),
            "month",
            lambda date: date.month,
        ),
        range_param(
            DateRange.THIS_YEAR,
            None,
            "year",
            lambda date: date.year,
            relativedelta(years=1),
        ),
        range_param(
            DateRange.LAST_YEAR,
            relativedelta(years=1),
            "year",
            lambda date: date.year,
        ),
        range_param(
            DateRange.THIS_QUARTER,
            None,
            "quarter",
            lambda date: get_quarter(date),
            relativedelta(months=3),
        ),
        range_param(
            DateRange.LAST_QUARTER,
            relativedelta(months=3),
            "quarter",
            lambda date: get_quarter(date),
        ),
    ],
)
def test_extract_ranges(
    engine, date_range, timedelta, previous_timedelta, extract, second_part, previous
):
    control = Control(date_range=date_range)
    query = slice_query(engine.data, "birthday", control, previous)
    timedelta = previous_timedelta if previous else timedelta
    date = TODAY - timedelta if timedelta else TODAY
    expected = engine.data[
        (engine.data.birthday.year() == date.year)
        & (getattr(engine.data.birthday, extract)() == second_part(date))
    ]

    assert query.equals(expected)


TODAY_LAST_QUARTER = TODAY - relativedelta(months=3)


@pytest.mark.parametrize("previous", [False, True], ids=["current", "previous"])
@pytest.mark.parametrize(
    "date_range, start, previous_start, previous_end",
    [
        pytest.param(
            DateRange.THIS_MONTH_UP_TO_DATE,
            TODAY.replace(day=1),
            (TODAY - relativedelta(months=1)).replace(day=1),
            (TODAY - relativedelta(months=1)),
            id="this month up to date",
        ),
        pytest.param(
            DateRange.LAST_FULL_12_MONTH,
            TODAY.replace(day=1) - relativedelta(months=12),
            (TODAY - relativedelta(months=24)).replace(day=1),
            TODAY - relativedelta(months=12),
            id="last full 12 month",
        ),
        pytest.param(
            DateRange.THIS_QUARTER_UP_TO_DATE,
            dt.date(
                TODAY_LAST_QUARTER.year,
                (get_quarter(TODAY_LAST_QUARTER)) * 3 + 1,
                1,
            ),
            dt.date(
                TODAY_LAST_QUARTER.year,
                (get_quarter(TODAY_LAST_QUARTER) - 1) * 3 + 1,
                1,
            ),
            TODAY_LAST_QUARTER,
            id="This quarter up to date",
        ),
    ],
)
def test_uptodate(engine, date_range, start, previous_start, previous_end, previous):
    control = Control(date_range=date_range)
    end = previous_end if previous else TODAY
    start = previous_start if previous else start
    query = slice_query(engine.data, "birthday", control, previous)
    expected = engine.data[engine.data.birthday.between(start, end)]
    assert query.equals(expected)


@pytest.mark.parametrize(
    "previous",
    [False, True],
    ids=["current", "previous"],
)
def test_this_year_up_to_date(engine, previous):
    control = Control(date_range=DateRange.THIS_YEAR_UP_TO_DATE)
    query = slice_query(engine.data, "birthday", control, previous)
    year = TODAY.year - 1 if previous else TODAY.year
    last_day = TODAY - relativedelta(years=1) if previous else TODAY
    expected = engine.data[
        (engine.data.birthday.year() == year) & (engine.data.birthday <= last_day)
    ]
    assert query.equals(expected)


@pytest.mark.parametrize(
    "previous",
    [False, True],
    ids=["current", "previous"],
)
def test_last_year(engine, previous):
    control = Control(date_range=DateRange.LAST_YEAR)
    query = slice_query(engine.data, "birthday", control, previous)
    last_year = TODAY.year - 2 if previous else TODAY.year - 1
    assert query.equals(engine.data[engine.data.birthday.year() == last_year])
