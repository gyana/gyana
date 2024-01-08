from datetime import date
from datetime import datetime as dt
from datetime import timedelta

import pytest
from dateutil.relativedelta import relativedelta
from ibis import bigquery

from apps.base.tests.mock_data import TABLE
from apps.filters.bigquery import get_quarter, get_query_from_filter
from apps.filters.models import DateRange, Filter

QUERY = """SELECT t0.*
FROM olympians t0
WHERE {}"""


def create_int_filter(operation):
    return Filter(
        column="id",
        type=Filter.Type.INTEGER,
        numeric_predicate=operation,
        integer_value=42,
    )


def create_float_filter(operation):
    return Filter(
        column="stars",
        type=Filter.Type.FLOAT,
        numeric_predicate=operation,
        float_value=42.0,
    )


def create_string_filter(operation):
    return Filter(
        column="athlete",
        type=Filter.Type.STRING,
        string_predicate=operation,
        string_value="Adam Ondra",
    )


def create_bool_filter(value):
    return Filter(
        column="is_nice",
        type=Filter.Type.BOOL,
        bool_predicate=value,
    )


def create_time_filter(operation):
    return Filter(
        column="lunch",
        type=Filter.Type.TIME,
        time_predicate=operation,
        time_value="11:11:11.1111",
    )


def create_date_filter(operation):
    return Filter(
        column="birthday",
        type=Filter.Type.DATE,
        datetime_predicate=operation,
        date_value="1993-07-26",
    )


def create_datetime_filter(operation):
    return Filter(
        column="when",
        type=Filter.Type.DATETIME,
        datetime_predicate=operation,
        datetime_value="1993-07-26T06:30:12.1234",
    )


TODAY = dt.today()
YEAR, WEEK, WEEKDAY = TODAY.isocalendar()
MONTH = TODAY.month
QUARTER = get_quarter(TODAY)

if WEEK == 1:
    LAST_WEEK = 52
    LAST_WEEK_YEAR = YEAR - 1
else:
    LAST_WEEK = WEEK - 1
    LAST_WEEK_YEAR = YEAR

if MONTH == 1:
    LAST_MONTH = 12
    LAST_MONTH_YEAR = YEAR - 1
else:
    LAST_MONTH = MONTH - 1
    LAST_MONTH_YEAR = YEAR


if QUARTER == 1:
    LAST_QUARTER = 4
    LAST_QUARTER_YEAR = YEAR - 1
else:
    LAST_QUARTER = QUARTER - 1
    LAST_QUARTER_YEAR = YEAR


def create_last_n_days(date_range, days):
    return pytest.param(
        create_date_filter(date_range),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY - timedelta(days=days)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id=f"Date on last {days}",
    )


PARAMS = [
    # Integer filters
    pytest.param(
        create_int_filter(Filter.NumericPredicate.EQUAL),
        QUERY.format("t0.`id` = 42"),
        id="Integer equal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.NEQUAL,
        ),
        QUERY.format("(t0.`id` != 42) OR (t0.`id` IS NULL)"),
        id="Integer not equal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.GREATERTHAN,
        ),
        QUERY.format("t0.`id` > 42"),
        id="Integer greaterthan",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.GREATERTHANEQUAL,
        ),
        QUERY.format("t0.`id` >= 42"),
        id="Integer greaterthanequal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.LESSTHAN,
        ),
        QUERY.format("t0.`id` < 42"),
        id="Integer lessthan",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.LESSTHANEQUAL,
        ),
        QUERY.format("t0.`id` <= 42"),
        id="Integer lessthanequal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.ISNULL,
        ),
        QUERY.format("t0.`id` IS NULL"),
        id="Integer is null",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.NOTNULL,
        ),
        QUERY.format("t0.`id` IS NOT NULL"),
        id="Integer not null",
    ),
    pytest.param(
        Filter(
            column="id",
            type=Filter.Type.INTEGER,
            numeric_predicate=Filter.NumericPredicate.ISIN,
            integer_values=[42, 43],
        ),
        QUERY.format("t0.`id` IN (42, 43)"),
        id="Integer is in",
    ),
    pytest.param(
        Filter(
            column="id",
            type=Filter.Type.INTEGER,
            numeric_predicate=Filter.NumericPredicate.NOTIN,
            integer_values=[42, 43],
        ),
        QUERY.format("t0.`id` NOT IN (42, 43) OR (t0.`id` IS NULL)"),
        id="Integer not in",
    ),
    # Float filters
    pytest.param(
        create_float_filter(Filter.NumericPredicate.EQUAL),
        QUERY.format("t0.`stars` = 42.0"),
        id="Float equal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.NEQUAL),
        QUERY.format("(t0.`stars` != 42.0) OR (t0.`stars` IS NULL)"),
        id="Float not equal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.GREATERTHAN),
        QUERY.format("t0.`stars` > 42.0"),
        id="Float greaterthan",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.GREATERTHANEQUAL),
        QUERY.format("t0.`stars` >= 42.0"),
        id="Float greaterthanequal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.LESSTHAN),
        QUERY.format("t0.`stars` < 42.0"),
        id="Float lessthan",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.LESSTHANEQUAL),
        QUERY.format("t0.`stars` <= 42.0"),
        id="Float lessthanequal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.ISNULL),
        QUERY.format("t0.`stars` IS NULL"),
        id="Float is null",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.NOTNULL),
        QUERY.format("t0.`stars` IS NOT NULL"),
        id="Float not null",
    ),
    pytest.param(
        Filter(
            column="stars",
            type=Filter.Type.FLOAT,
            numeric_predicate=Filter.NumericPredicate.ISIN,
            float_values=[42.0, 42.3],
        ),
        QUERY.format("t0.`stars` IN (42.0, 42.3)"),
        id="Float is in",
    ),
    pytest.param(
        Filter(
            column="stars",
            type=Filter.Type.FLOAT,
            numeric_predicate=Filter.NumericPredicate.NOTIN,
            float_values=[42.0, 42.3],
        ),
        QUERY.format("t0.`stars` NOT IN (42.0, 42.3) OR (t0.`stars` IS NULL)"),
        id="Float not in",
    ),
    # String filters
    pytest.param(
        create_string_filter(Filter.StringPredicate.EQUAL),
        QUERY.format("t0.`athlete` = 'Adam Ondra'"),
        id="String equal",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NEQUAL),
        QUERY.format("(t0.`athlete` != 'Adam Ondra') OR (t0.`athlete` IS NULL)"),
        id="String not equal",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.CONTAINS),
        QUERY.format("STRPOS(t0.`athlete`, 'Adam Ondra') - 1 >= 0"),
        id="String contains",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NOTCONTAINS),
        QUERY.format("NOT STRPOS(t0.`athlete`, 'Adam Ondra') - 1 >= 0"),
        id="String not contains",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.STARTSWITH),
        QUERY.format("t0.`athlete` like concat('Adam Ondra', '%')"),
        id="String starts with",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ENDSWITH),
        QUERY.format("t0.`athlete` like concat('%', 'Adam Ondra')"),
        id="String ends with",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISNULL),
        QUERY.format("t0.`athlete` IS NULL"),
        id="String is null",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NOTNULL),
        QUERY.format("t0.`athlete` IS NOT NULL"),
        id="String not null",
    ),
    pytest.param(
        Filter(
            column="athlete",
            type=Filter.Type.STRING,
            string_predicate=Filter.StringPredicate.ISIN,
            string_values=["Janja Garnbret"],
        ),
        QUERY.format("t0.`athlete` IN ('Janja Garnbret')"),
        id="String is in",
    ),
    pytest.param(
        Filter(
            column="athlete",
            type=Filter.Type.STRING,
            string_predicate=Filter.StringPredicate.NOTIN,
            string_values=["Janja Garnbret"],
        ),
        QUERY.format(
            "t0.`athlete` NOT IN ('Janja Garnbret') OR (t0.`athlete` IS NULL)"
        ),
        id="String not in",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISUPPERCASE),
        QUERY.format("t0.`athlete` = upper(t0.`athlete`)"),
        id="String is uppercase",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISLOWERCASE),
        QUERY.format("t0.`athlete` = lower(t0.`athlete`)"),
        id="String is lowercase",
    ),
    # Bool filter
    pytest.param(
        create_bool_filter(Filter.BoolPredicate.ISTRUE),
        QUERY.format("t0.`is_nice`"),
        id="Bool is true",
    ),
    pytest.param(
        create_bool_filter(Filter.BoolPredicate.ISFALSE),
        QUERY.format("t0.`is_nice` = FALSE"),
        id="Bool is false",
    ),
    # Time filter
    pytest.param(
        create_time_filter(Filter.TimePredicate.ON),
        QUERY.format("t0.`lunch` = '11:11:11.1111'"),
        id="Time on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.NOTON),
        QUERY.format("(t0.`lunch` != '11:11:11.1111') OR (t0.`lunch` IS NULL)"),
        id="Time not on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.BEFORE),
        QUERY.format("t0.`lunch` < '11:11:11.1111'"),
        id="Time before",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.BEFOREON),
        QUERY.format("t0.`lunch` <= '11:11:11.1111'"),
        id="Time before on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.AFTER),
        QUERY.format("t0.`lunch` > '11:11:11.1111'"),
        id="Time after",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.AFTERON),
        QUERY.format("t0.`lunch` >= '11:11:11.1111'"),
        id="Time after on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.ISNULL),
        QUERY.format("t0.`lunch` IS NULL"),
        id="Time is null",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.NOTNULL),
        QUERY.format("t0.`lunch` IS NOT NULL"),
        id="Time not null",
    ),
    # Date filters
    pytest.param(
        create_date_filter(Filter.TimePredicate.ON),
        QUERY.format("t0.`birthday` = '1993-07-26'"),
        id="Date on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.NOTON),
        QUERY.format("(t0.`birthday` != '1993-07-26') OR (t0.`birthday` IS NULL)"),
        id="Date not on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.BEFORE),
        QUERY.format("t0.`birthday` < '1993-07-26'"),
        id="Date before",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.BEFOREON),
        QUERY.format("t0.`birthday` <= '1993-07-26'"),
        id="Date before on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.AFTER),
        QUERY.format("t0.`birthday` > '1993-07-26'"),
        id="Date after",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.AFTERON),
        QUERY.format("t0.`birthday` >= '1993-07-26'"),
        id="Date after on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.ISNULL),
        QUERY.format("t0.`birthday` IS NULL"),
        id="Date is null",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.NOTNULL),
        QUERY.format("t0.`birthday` IS NOT NULL"),
        id="Date not null",
    ),
    pytest.param(
        create_date_filter(DateRange.TODAY),
        QUERY.format(f"t0.`birthday` = DATE '{TODAY.strftime('%Y-%m-%d')}'"),
        id="Date today",
    ),
    pytest.param(
        create_date_filter(DateRange.TOMORROW),
        QUERY.format(
            f"t0.`birthday` = DATE '{(TODAY + timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Date tomorrow",
    ),
    pytest.param(
        create_date_filter(DateRange.YESTERDAY),
        QUERY.format(
            f"t0.`birthday` = DATE '{(TODAY - timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Date yesterday",
    ),
    pytest.param(
        create_date_filter(DateRange.ONEWEEKAGO),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY - timedelta(days=7)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date one week ago",
    ),
    pytest.param(
        create_date_filter(DateRange.ONEMONTHAGO),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date one month ago",
    ),
    pytest.param(
        create_date_filter(DateRange.ONEYEARAGO),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY - relativedelta(years=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date one year ago",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_WEEK),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {YEAR}) AND\n      (EXTRACT(ISOWEEK from t0.`birthday`) = {WEEK})"
        ),
        id="Date on this week",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_WEEK_UP_TO_DATE),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY - timedelta(days=TODAY.weekday())).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on this week up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_WEEK),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {LAST_WEEK_YEAR}) AND\n      (EXTRACT(ISOWEEK from t0.`birthday`) = {LAST_WEEK})"
        ),
        id="Date on last week",
    ),
    create_last_n_days(DateRange.LAST_7, 7),
    create_last_n_days(DateRange.LAST_14, 14),
    create_last_n_days(DateRange.LAST_28, 28),
    create_last_n_days(DateRange.LAST_30, 30),
    create_last_n_days(DateRange.LAST_90, 90),
    create_last_n_days(DateRange.LAST_180, 180),
    pytest.param(
        create_date_filter(DateRange.THIS_MONTH),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {YEAR}) AND\n      (EXTRACT(month from t0.`birthday`) = {MONTH})"
        ),
        id="Date on this month",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_MONTH_UP_TO_DATE),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY.replace(day=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on this month up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_MONTH),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {LAST_MONTH_YEAR}) AND\n      (EXTRACT(month from t0.`birthday`) = {LAST_MONTH})"
        ),
        id="Date on last month",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_YEAR),
        QUERY.format(f"EXTRACT(year from t0.`birthday`) = {YEAR }"),
        id="Date on this year",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_YEAR_UP_TO_DATE),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {YEAR }) AND\n      (t0.`birthday` <= DATE '{TODAY.strftime('%Y-%m-%d')}')"
        ),
        id="Date on this year up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_YEAR),
        QUERY.format(f"EXTRACT(year from t0.`birthday`) = {YEAR -1}"),
        id="Date on last year",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_QUARTER),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {YEAR}) AND\n      (EXTRACT(quarter from t0.`birthday`) = {QUARTER})"
        ),
        id="Date on this quarter",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_QUARTER_UP_TO_DATE),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{date(TODAY.year, (QUARTER-1)*3+1, 1).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on this quarter up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_QUARTER),
        QUERY.format(
            f"(EXTRACT(year from t0.`birthday`) = {LAST_QUARTER_YEAR}) AND\n      (EXTRACT(quarter from t0.`birthday`) = {LAST_QUARTER})"
        ),
        id="Date on last quarter",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_12_MONTH),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=12)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on last 12 month",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_FULL_12_MONTH),
        QUERY.format(
            f"t0.`birthday` BETWEEN DATE '{(TODAY.replace(day=1) - relativedelta(months=12)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on last full 12 month",
    ),
    # Datetime filters
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.ON),
        QUERY.format("t0.`when` = '1993-07-26T06:30:12.1234'"),
        id="Dateime on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.NOTON),
        QUERY.format(
            "(t0.`when` != '1993-07-26T06:30:12.1234') OR (t0.`when` IS NULL)"
        ),
        id="Dateime not on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.BEFORE),
        QUERY.format("t0.`when` < '1993-07-26T06:30:12.1234'"),
        id="Dateime before",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.BEFOREON),
        QUERY.format("t0.`when` <= '1993-07-26T06:30:12.1234'"),
        id="Dateime before on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.AFTER),
        QUERY.format("t0.`when` > '1993-07-26T06:30:12.1234'"),
        id="Dateime after",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.AFTERON),
        QUERY.format("t0.`when` >= '1993-07-26T06:30:12.1234'"),
        id="Dateime after on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.ISNULL),
        QUERY.format("t0.`when` IS NULL"),
        id="Dateime is null",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.NOTNULL),
        QUERY.format("t0.`when` IS NOT NULL"),
        id="Dateime not null",
    ),
    pytest.param(
        create_datetime_filter(DateRange.TODAY),
        QUERY.format(f"DATE(t0.`when`) = DATE '{TODAY.strftime('%Y-%m-%d')}'"),
        id="Datetime today",
    ),
    pytest.param(
        create_datetime_filter(DateRange.TOMORROW),
        QUERY.format(
            f"DATE(t0.`when`) = DATE '{(TODAY + timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Datetime tomorrow",
    ),
    pytest.param(
        create_datetime_filter(DateRange.YESTERDAY),
        QUERY.format(
            f"DATE(t0.`when`) = DATE '{(TODAY - timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Datetime yesterday",
    ),
    pytest.param(
        create_datetime_filter(DateRange.ONEWEEKAGO),
        QUERY.format(
            f"DATE(t0.`when`) BETWEEN DATE '{(TODAY - timedelta(days=7)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Datetime one week ago",
    ),
    pytest.param(
        create_datetime_filter(DateRange.ONEMONTHAGO),
        QUERY.format(
            f"DATE(t0.`when`) BETWEEN DATE '{(TODAY - relativedelta(months=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Datetime one month ago",
    ),
    pytest.param(
        create_datetime_filter(DateRange.ONEYEARAGO),
        QUERY.format(
            f"DATE(t0.`when`) BETWEEN DATE '{(TODAY - relativedelta(years=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Datetime one year ago",
    ),
]


@pytest.mark.parametrize("filter_, expected_sql", PARAMS)
def test_compiles_filter(filter_, expected_sql):
    sql = bigquery.compile(get_query_from_filter(TABLE, filter_))
    assert sql == expected_sql


def get_predicate(param):
    f = param.values[0]

    return (
        f.numeric_predicate
        or f.time_predicate
        or f.datetime_predicate
        or f.string_predicate
    )


def test_all_filters_tested():
    tested = set(map(get_predicate, PARAMS))
    # Boolean test has no  predicate
    assert tested == {
        None,
        *DateRange,
        *Filter.NumericPredicate,
        *Filter.StringPredicate,
        *Filter.TimePredicate,
    }
