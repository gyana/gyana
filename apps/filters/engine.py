import datetime as dt
from functools import reduce
from inspect import signature
from typing import List

from dateutil.relativedelta import relativedelta
from ibis.expr.types import TimestampValue

from apps.controls.engine import DATETIME_FILTERS
from apps.filters.models import PREDICATE_MAP, Filter


def eq(query, column, value):
    return query[query[column] == value]


def neq(query, column, value):
    return query[(query[column] != value) | query[column].isnull()]


def gt(query, column, value):
    return query[query[column] > value]


def gte(query, column, value):
    return query[query[column] >= value]


def lt(query, column, value):
    return query[query[column] < value]


def lte(query, column, value):
    return query[query[column] <= value]


def isnull(query, column):
    return query[query[column].isnull()]


def notnull(query, column):
    return query[query[column].notnull()]


def isin(query, column, values):
    return query[query[column].isin(values)]


def notin(query, column, values):
    return query[(query[column].notin(values)) | (query[column].isnull())]


def contains(query, column, value):
    return query[query[column].contains(value)]


def not_contains(query, column, value):
    return query[~query[column].contains(value)]


def startswith(query, column, value):
    return query[query[column].startswith(value)]


def endswith(query, column, value):
    return query[query[column].endswith(value)]


def islower(query, column):
    return query[query[column] == query[column].lower()]


def isupper(query, column):
    return query[query[column] == query[column].upper()]


def is_true(query, column):
    return query[query[column]]


def is_false(query, column):
    return query[query[column] == False]


def get_date(column):
    if isinstance(column, TimestampValue):
        return column.date()
    return column


def today(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    return query[date == today]


def tomorrow(query, column):
    date = get_date(query[column])
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    return query[date == tomorrow]


def yesterday(query, column):
    date = get_date(query[column])
    yesterday_ = dt.date.today() - dt.timedelta(days=1)
    return query[date == yesterday_]


def one_week_ago(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    one_week = today - dt.timedelta(days=7)
    return query[date.between(one_week, today)]


def one_month_ago(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    one_month = today - relativedelta(months=1)
    return query[date.between(one_month, today)]


def one_year_ago(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    one_year = today - relativedelta(years=1)
    return query[date.between(one_year, today)]


def this_week(query, column):
    date = get_date(query[column])
    year, week, _ = dt.date.today().isocalendar()
    return query[(date.year() == year) & (date.week_of_year() == week)]


def this_week_up_todate(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    start_of_week = today - dt.timedelta(days=today.weekday())
    return query[date.between(start_of_week, today)]


def last_week(query, column):
    date = get_date(query[column])
    year, week, _ = (dt.date.today() - dt.timedelta(days=7)).isocalendar()
    return query[(date.year() == year) & (date.week_of_year() == week)]


def last_n_days(query, column, days):
    date = get_date(query[column])
    today = dt.date.today()
    n_days_ago = today - dt.timedelta(days=days)
    return query[date.between(n_days_ago, today)]


def this_month(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    return query[(date.year() == today.year) & (date.month() == today.month)]


def this_month_up_to_date(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    return query[date.between(today.replace(day=1), today)]


def last_month(query, column):
    date = get_date(query[column])
    last_month = dt.date.today() - relativedelta(months=1)
    return query[(date.year() == last_month.year) & (date.month() == last_month.month)]


def get_quarter(date):
    return (date.month - 1) // 3 + 1


def this_quarter(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    quarter = get_quarter(today)

    return query[(date.year() == today.year) & (date.quarter() == quarter)]


def this_quarter_up_to_date(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    quarter = get_quarter(today)

    return query[date.between(dt.date(today.year, (quarter - 1) * 3 + 1, 1), today)]


def last_quarter(query, column):
    date = get_date(query[column])
    today_last_quarter = dt.date.today() - relativedelta(months=3)
    quarter = get_quarter(today_last_quarter)

    return query[(date.year() == today_last_quarter.year) & (date.quarter() == quarter)]


def this_year(query, column):
    date = get_date(query[column])
    year = dt.date.today().year
    return query[date.year() == year]


def this_year_up_todate(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    return query[(date.year() == today.year) & (date <= today)]


def last_12_month(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    twelve_month_ago = today - relativedelta(months=12)
    return query[date.between(twelve_month_ago, today)]


def last_full_12_month(query, column):
    today = dt.date.today()
    date = get_date(query[column])
    twelve_month_ago = (today - relativedelta(months=12)).replace(day=1)
    return query[date.between(twelve_month_ago, today)]


def last_year(query, column):
    date = get_date(query[column])
    last_year = (dt.date.today() - relativedelta(years=1)).year
    return query[date.year() == last_year]


FILTER_MAP = {
    Filter.StringPredicate.EQUAL: eq,
    Filter.StringPredicate.NEQUAL: neq,
    Filter.StringPredicate.CONTAINS: contains,
    Filter.StringPredicate.NOTCONTAINS: not_contains,
    Filter.StringPredicate.ISNULL: isnull,
    Filter.StringPredicate.NOTNULL: notnull,
    Filter.StringPredicate.STARTSWITH: startswith,
    Filter.StringPredicate.ENDSWITH: endswith,
    Filter.StringPredicate.ISUPPERCASE: isupper,
    Filter.StringPredicate.ISLOWERCASE: islower,
    Filter.NumericPredicate.GREATERTHAN: gt,
    Filter.NumericPredicate.GREATERTHANEQUAL: gte,
    Filter.NumericPredicate.LESSTHAN: lt,
    Filter.NumericPredicate.LESSTHANEQUAL: lte,
    Filter.NumericPredicate.ISIN: isin,
    Filter.NumericPredicate.NOTIN: notin,
    Filter.BoolPredicate.ISFALSE: is_false,
    Filter.BoolPredicate.ISTRUE: is_true,
    **{key: value["function"] for key, value in DATETIME_FILTERS.items()},
}


def get_query_from_filter(query, filter_: Filter):
    column = filter_.column
    predicate = getattr(filter_, PREDICATE_MAP[filter_.type])

    func = FILTER_MAP[predicate]
    func_params = signature(func).parameters
    if "value" not in func_params and "values" not in func_params:
        return func(query, column)

    value_str = "values" if predicate in ["isin", "notin"] else "value"
    value = getattr(filter_, f"{filter_.type.lower()}_{value_str}")
    return func(query, column, value)


def get_query_from_filters(query, filters: List[Filter]):
    return reduce(
        get_query_from_filter,
        filters,
        query,
    )
