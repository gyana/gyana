from datetime import date
from datetime import datetime as dt
from datetime import timedelta

import ibis_bigquery
import pytest
from dateutil.relativedelta import relativedelta

from apps.base.tests.mock_data import TABLE
from apps.filters.bigquery import get_quarter, get_query_from_filter
from apps.filters.forms import FilterForm
from apps.filters.models import DateRange, Filter

QUERY = """SELECT *
FROM olympians
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
        bool_value=value,
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
        column="updated",
        type=Filter.Type.DATETIME,
        datetime_predicate=operation,
        datetime_value="1993-07-26T06:30:12.1234",
    )


TODAY = dt.today()
YEAR, WEEK, WEEKDAY = TODAY.isocalendar()
MONTH = TODAY.month
QUARTER = get_quarter(TODAY)

if WEEK == 1:
    LAST_WEEK = 53
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
            f"`birthday` BETWEEN DATE '{(TODAY - timedelta(days=days)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id=f"Date on last {days}",
    )


PARAMS = [
    # Integer filters
    pytest.param(
        create_int_filter(Filter.NumericPredicate.EQUAL),
        QUERY.format("`id` = 42"),
        id="Integer equal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.NEQUAL,
        ),
        QUERY.format("`id` != 42"),
        id="Integer not equal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.GREATERTHAN,
        ),
        QUERY.format("`id` > 42"),
        id="Integer greaterthan",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.GREATERTHANEQUAL,
        ),
        QUERY.format("`id` >= 42"),
        id="Integer greaterthanequal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.LESSTHAN,
        ),
        QUERY.format("`id` < 42"),
        id="Integer lessthan",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.LESSTHANEQUAL,
        ),
        QUERY.format("`id` <= 42"),
        id="Integer lessthanequal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.ISNULL,
        ),
        QUERY.format("`id` IS NULL"),
        id="Integer is null",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.NOTNULL,
        ),
        QUERY.format("`id` IS NOT NULL"),
        id="Integer not null",
    ),
    pytest.param(
        Filter(
            column="id",
            type=Filter.Type.INTEGER,
            numeric_predicate=Filter.NumericPredicate.ISIN,
            integer_values=[42, 43],
        ),
        QUERY.format("`id` IN (42, 43)"),
        id="Integer is in",
    ),
    pytest.param(
        Filter(
            column="id",
            type=Filter.Type.INTEGER,
            numeric_predicate=Filter.NumericPredicate.NOTIN,
            integer_values=[42, 43],
        ),
        QUERY.format("`id` NOT IN (42, 43)"),
        id="Integer not in",
    ),
    # Float filters
    pytest.param(
        create_float_filter(Filter.NumericPredicate.EQUAL),
        QUERY.format("`stars` = 42.0"),
        id="Float equal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.NEQUAL),
        QUERY.format("`stars` != 42.0"),
        id="Float not equal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.GREATERTHAN),
        QUERY.format("`stars` > 42.0"),
        id="Float greaterthan",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.GREATERTHANEQUAL),
        QUERY.format("`stars` >= 42.0"),
        id="Float greaterthanequal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.LESSTHAN),
        QUERY.format("`stars` < 42.0"),
        id="Float lessthan",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.LESSTHANEQUAL),
        QUERY.format("`stars` <= 42.0"),
        id="Float lessthanequal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.ISNULL),
        QUERY.format("`stars` IS NULL"),
        id="Float is null",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.NOTNULL),
        QUERY.format("`stars` IS NOT NULL"),
        id="Float not null",
    ),
    pytest.param(
        Filter(
            column="stars",
            type=Filter.Type.FLOAT,
            numeric_predicate=Filter.NumericPredicate.ISIN,
            float_values=[42.0, 42.3],
        ),
        QUERY.format("`stars` IN (42.0, 42.3)"),
        id="Float is in",
    ),
    pytest.param(
        Filter(
            column="stars",
            type=Filter.Type.FLOAT,
            numeric_predicate=Filter.NumericPredicate.NOTIN,
            float_values=[42.0, 42.3],
        ),
        QUERY.format("`stars` NOT IN (42.0, 42.3)"),
        id="Float not in",
    ),
    # String filters
    pytest.param(
        create_string_filter(Filter.StringPredicate.EQUAL),
        QUERY.format("`athlete` = 'Adam Ondra'"),
        id="String equal",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NEQUAL),
        QUERY.format("`athlete` != 'Adam Ondra'"),
        id="String not equal",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.CONTAINS),
        QUERY.format("STRPOS(`athlete`, 'Adam Ondra') - 1 >= 0"),
        id="String contains",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NOTCONTAINS),
        QUERY.format("NOT (STRPOS(`athlete`, 'Adam Ondra') - 1 >= 0)"),
        id="String not contains",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.STARTSWITH),
        QUERY.format("STARTS_WITH(`athlete`, 'Adam Ondra')"),
        id="String starts with",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ENDSWITH),
        QUERY.format("ENDS_WITH(`athlete`, 'Adam Ondra')"),
        id="String ends with",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISNULL),
        QUERY.format("`athlete` IS NULL"),
        id="String is null",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NOTNULL),
        QUERY.format("`athlete` IS NOT NULL"),
        id="String not null",
    ),
    pytest.param(
        Filter(
            column="athlete",
            type=Filter.Type.STRING,
            string_predicate=Filter.StringPredicate.ISIN,
            string_values=["Janja Garnbret"],
        ),
        QUERY.format("`athlete` IN ('Janja Garnbret')"),
        id="String is in",
    ),
    pytest.param(
        Filter(
            column="athlete",
            type=Filter.Type.STRING,
            string_predicate=Filter.StringPredicate.NOTIN,
            string_values=["Janja Garnbret"],
        ),
        QUERY.format("`athlete` NOT IN ('Janja Garnbret')"),
        id="String not in",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISUPPERCASE),
        QUERY.format("`athlete` = upper(`athlete`)"),
        id="String is uppercase",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISLOWERCASE),
        QUERY.format("`athlete` = lower(`athlete`)"),
        id="String is lowercase",
    ),
    # Bool filter
    pytest.param(
        create_bool_filter(True),
        QUERY.format("`is_nice` = TRUE"),
        id="Bool is true",
    ),
    pytest.param(
        create_bool_filter(False),
        QUERY.format("`is_nice` = FALSE"),
        id="Bool is false",
    ),
    # Time filter
    pytest.param(
        create_time_filter(Filter.TimePredicate.ON),
        QUERY.format("`lunch` = TIME '11:11:11.1111'"),
        id="Time on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.NOTON),
        QUERY.format("`lunch` != TIME '11:11:11.1111'"),
        id="Time not on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.BEFORE),
        QUERY.format("`lunch` < TIME '11:11:11.1111'"),
        id="Time before",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.BEFOREON),
        QUERY.format("`lunch` <= TIME '11:11:11.1111'"),
        id="Time before on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.AFTER),
        QUERY.format("`lunch` > TIME '11:11:11.1111'"),
        id="Time after",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.AFTERON),
        QUERY.format("`lunch` >= TIME '11:11:11.1111'"),
        id="Time after on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.ISNULL),
        QUERY.format("`lunch` IS NULL"),
        id="Time is null",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.NOTNULL),
        QUERY.format("`lunch` IS NOT NULL"),
        id="Time not null",
    ),
    # Date filters
    pytest.param(
        create_date_filter(Filter.TimePredicate.ON),
        QUERY.format("`birthday` = DATE '1993-07-26'"),
        id="Date on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.NOTON),
        QUERY.format("`birthday` != DATE '1993-07-26'"),
        id="Date not on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.BEFORE),
        QUERY.format("`birthday` < DATE '1993-07-26'"),
        id="Date before",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.BEFOREON),
        QUERY.format("`birthday` <= DATE '1993-07-26'"),
        id="Date before on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.AFTER),
        QUERY.format("`birthday` > DATE '1993-07-26'"),
        id="Date after",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.AFTERON),
        QUERY.format("`birthday` >= DATE '1993-07-26'"),
        id="Date after on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.ISNULL),
        QUERY.format("`birthday` IS NULL"),
        id="Date is null",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.NOTNULL),
        QUERY.format("`birthday` IS NOT NULL"),
        id="Date not null",
    ),
    pytest.param(
        create_date_filter(DateRange.TODAY),
        QUERY.format(f"`birthday` = DATE '{TODAY.strftime('%Y-%m-%d')}'"),
        id="Date today",
    ),
    pytest.param(
        create_date_filter(DateRange.TOMORROW),
        QUERY.format(
            f"`birthday` = DATE '{(TODAY + timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Date tomorrow",
    ),
    pytest.param(
        create_date_filter(DateRange.YESTERDAY),
        QUERY.format(
            f"`birthday` = DATE '{(TODAY - timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Date yesterday",
    ),
    pytest.param(
        create_date_filter(DateRange.ONEWEEKAGO),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY - timedelta(days=7)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date one week ago",
    ),
    pytest.param(
        create_date_filter(DateRange.ONEMONTHAGO),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date one month ago",
    ),
    pytest.param(
        create_date_filter(DateRange.ONEYEARAGO),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(years=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date one year ago",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_WEEK),
        QUERY.format(
            f"(EXTRACT(year from `birthday`) = {YEAR}) AND\n      (ISOWEEK `birthday` = {WEEK})"
        ),
        id="Date on this week",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_WEEK_UP_TO_DATE),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY - timedelta(days=TODAY.weekday())).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on this week up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_WEEK),
        QUERY.format(
            f"(EXTRACT(year from `birthday`) = {LAST_WEEK_YEAR}) AND\n      (ISOWEEK `birthday` = {LAST_WEEK})"
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
            f"(EXTRACT(year from `birthday`) = {YEAR}) AND\n      (EXTRACT(month from `birthday`) = {MONTH})"
        ),
        id="Date on this month",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_MONTH_UP_TO_DATE),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY.replace(day=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on this month up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_MONTH),
        QUERY.format(
            f"(EXTRACT(year from `birthday`) = {LAST_MONTH_YEAR}) AND\n      (EXTRACT(month from `birthday`) = {LAST_MONTH})"
        ),
        id="Date on last month",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_YEAR),
        QUERY.format(f"EXTRACT(year from `birthday`) = {YEAR }"),
        id="Date on this year",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_YEAR_UP_TO_DATE),
        QUERY.format(
            f"(EXTRACT(year from `birthday`) = {YEAR }) AND\n      (`birthday` <= DATE '2021-12-03')"
        ),
        id="Date on this year up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_YEAR),
        QUERY.format(f"EXTRACT(year from `birthday`) = {YEAR -1}"),
        id="Date on last year",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_QUARTER),
        QUERY.format(
            f"(EXTRACT(year from `birthday`) = {YEAR}) AND\n      (EXTRACT(quarter from `birthday`) = {QUARTER})"
        ),
        id="Date on this quarter",
    ),
    pytest.param(
        create_date_filter(DateRange.THIS_QUARTER_UP_TO_DATE),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{date(TODAY.year, (QUARTER-1)*3+1, 1).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on this quarter up to date",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_QUARTER),
        QUERY.format(
            f"(EXTRACT(year from `birthday`) = {LAST_QUARTER_YEAR}) AND\n      (EXTRACT(quarter from `birthday`) = {LAST_QUARTER})"
        ),
        id="Date on last quarter",
    ),
    pytest.param(
        create_date_filter(DateRange.LAST_12_MONTH),
        QUERY.format(
            f"`birthday` BETWEEN DATE '{(TODAY - relativedelta(months=12)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Date on last 12 month",
    ),
    # Datetime filters
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.ON),
        QUERY.format("`updated` = TIMESTAMP '1993-07-26T06:30:12.1234'"),
        id="Dateime on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.NOTON),
        QUERY.format("`updated` != TIMESTAMP '1993-07-26T06:30:12.1234'"),
        id="Dateime not on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.BEFORE),
        QUERY.format("`updated` < TIMESTAMP '1993-07-26T06:30:12.1234'"),
        id="Dateime before",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.BEFOREON),
        QUERY.format("`updated` <= TIMESTAMP '1993-07-26T06:30:12.1234'"),
        id="Dateime before on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.AFTER),
        QUERY.format("`updated` > TIMESTAMP '1993-07-26T06:30:12.1234'"),
        id="Dateime after",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.AFTERON),
        QUERY.format("`updated` >= TIMESTAMP '1993-07-26T06:30:12.1234'"),
        id="Dateime after on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.ISNULL),
        QUERY.format("`updated` IS NULL"),
        id="Dateime is null",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.NOTNULL),
        QUERY.format("`updated` IS NOT NULL"),
        id="Dateime not null",
    ),
    pytest.param(
        create_datetime_filter(DateRange.TODAY),
        QUERY.format(f"DATE(`updated`) = DATE '{TODAY.strftime('%Y-%m-%d')}'"),
        id="Datetime today",
    ),
    pytest.param(
        create_datetime_filter(DateRange.TOMORROW),
        QUERY.format(
            f"DATE(`updated`) = DATE '{(TODAY + timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Datetime tomorrow",
    ),
    pytest.param(
        create_datetime_filter(DateRange.YESTERDAY),
        QUERY.format(
            f"DATE(`updated`) = DATE '{(TODAY - timedelta(days=1)).strftime('%Y-%m-%d')}'"
        ),
        id="Datetime yesterday",
    ),
    pytest.param(
        create_datetime_filter(DateRange.ONEWEEKAGO),
        QUERY.format(
            f"DATE(`updated`) BETWEEN DATE '{(TODAY - timedelta(days=7)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Datetime one week ago",
    ),
    pytest.param(
        create_datetime_filter(DateRange.ONEMONTHAGO),
        QUERY.format(
            f"DATE(`updated`) BETWEEN DATE '{(TODAY - relativedelta(months=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Datetime one month ago",
    ),
    pytest.param(
        create_datetime_filter(DateRange.ONEYEARAGO),
        QUERY.format(
            f"DATE(`updated`) BETWEEN DATE '{(TODAY - relativedelta(years=1)).strftime('%Y-%m-%d')}' AND DATE '{TODAY.strftime('%Y-%m-%d')}'"
        ),
        id="Datetime one year ago",
    ),
]


@pytest.mark.parametrize("filter_, expected_sql", PARAMS)
def test_compiles_filter(filter_, expected_sql):
    sql = ibis_bigquery.compile(get_query_from_filter(TABLE, filter_))
    assert sql == expected_sql


@pytest.mark.parametrize(
    "filter_, fields",
    [
        pytest.param(Filter(), ["column"], id="empty filter"),
        pytest.param(
            Filter(column="id"), ["column", "numeric_predicate"], id="Integer column"
        ),
        pytest.param(
            Filter(column="id", numeric_predicate="isin"),
            ["column", "numeric_predicate", "integer_values"],
            id="Integer column with isin predicate",
        ),
        pytest.param(
            Filter(column="id", numeric_predicate="equal"),
            ["column", "numeric_predicate", "integer_value"],
            id="Integer column with predicate",
        ),
        pytest.param(
            Filter(column="stars"), ["column", "numeric_predicate"], id="Float column"
        ),
        pytest.param(
            Filter(column="stars", numeric_predicate="equal"),
            ["column", "numeric_predicate", "float_value"],
            id="Float column with predicate",
        ),
        pytest.param(
            Filter(column="stars", numeric_predicate="isin"),
            ["column", "numeric_predicate", "float_values"],
            id="Float column with isin predicate",
        ),
        pytest.param(
            Filter(column="athlete"), ["column", "string_predicate"], id="String column"
        ),
        pytest.param(
            Filter(column="athlete", string_predicate="equal"),
            ["column", "string_predicate", "string_value"],
            id="String column with predicate",
        ),
        pytest.param(
            Filter(column="athlete", string_predicate="isin"),
            ["column", "string_predicate", "string_values"],
            id="String column with isin predicate",
        ),
        pytest.param(
            Filter(column="is_nice"), ["column", "bool_value"], id="Bool column"
        ),
        pytest.param(
            Filter(column="birthday"),
            ["column", "datetime_predicate"],
            id="Date column",
        ),
        pytest.param(
            Filter(column="birthday", datetime_predicate="equal"),
            ["column", "datetime_predicate", "date_value"],
            id="Date column with predicate",
        ),
        pytest.param(
            Filter(column="lunch"), ["column", "time_predicate"], id="Time column"
        ),
        pytest.param(
            Filter(column="lunch", time_predicate="equal"),
            ["column", "time_predicate", "time_value"],
            id="Time column with predicate",
        ),
        pytest.param(
            Filter(column="updated"),
            ["column", "datetime_predicate"],
            id="Datetime column",
        ),
        pytest.param(
            Filter(column="updated", datetime_predicate="equal"),
            ["column", "datetime_predicate", "datetime_value"],
            id="Datetime column with predicate",
        ),
    ],
)
def test_filter_type_functions(filter_, fields):
    form = FilterForm(schema=TABLE.schema(), instance=filter_)
    assert form.get_live_fields() == fields


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
