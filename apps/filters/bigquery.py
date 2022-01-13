import datetime as dt
from functools import partial, reduce
from inspect import signature
from typing import List

from dateutil.relativedelta import relativedelta
from ibis.expr.types import TimestampValue

from apps.filters.models import PREDICATE_MAP, DateRange, Filter


def eq(query, column, value):
    return query[query[column] == value]


def neq(query, column, value):
    return query[query[column] != value]


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
    return query[query[column].notin(values)]


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
    return query[(date.year() == year) & (date.isoweek() == week)]


def this_week_up_todate(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    start_of_week = today - dt.timedelta(days=today.weekday())
    return query[date.between(start_of_week, today)]


def last_week(query, column):
    date = get_date(query[column])
    year, week, _ = (dt.date.today() - dt.timedelta(days=7)).isocalendar()
    return query[(date.year() == year) & (date.isoweek() == week)]


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
    today = dt.date.today()
    quarter = get_quarter(today)

    if quarter == 1:
        quarter = 4
        year = today.year - 1
    else:
        quarter = quarter - 1
        year = today.year
    return query[(date.year() == year) & (date.quarter() == quarter)]


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


def filter_boolean(query, column, value):
    return query[query[column] == value]


DATETIME_FILTERS = {
    DateRange.TODAY: today,
    DateRange.TOMORROW: tomorrow,
    DateRange.YESTERDAY: yesterday,
    DateRange.ONEWEEKAGO: one_week_ago,
    DateRange.ONEMONTHAGO: one_month_ago,
    DateRange.ONEYEARAGO: one_year_ago,
    DateRange.THIS_WEEK: this_week,
    DateRange.THIS_WEEK_UP_TO_DATE: this_week_up_todate,
    DateRange.LAST_WEEK: last_week,
    DateRange.LAST_7: partial(last_n_days, days=7),
    DateRange.LAST_14: partial(last_n_days, days=14),
    DateRange.LAST_28: partial(last_n_days, days=28),
    DateRange.LAST_30: partial(last_n_days, days=30),
    DateRange.THIS_MONTH: this_month,
    DateRange.THIS_MONTH_UP_TO_DATE: this_month_up_to_date,
    DateRange.LAST_MONTH: last_month,
    DateRange.LAST_90: partial(last_n_days, days=90),
    DateRange.THIS_QUARTER: this_quarter,
    DateRange.THIS_QUARTER_UP_TO_DATE: this_quarter_up_to_date,
    DateRange.LAST_QUARTER: last_quarter,
    DateRange.LAST_180: partial(last_n_days, days=180),
    DateRange.THIS_YEAR: this_year,
    DateRange.THIS_YEAR_UP_TO_DATE: this_year_up_todate,
    DateRange.LAST_12_MONTH: last_12_month,
    DateRange.LAST_FULL_12_MONTH: last_full_12_month,
    DateRange.LAST_YEAR: last_year,
}


def previous_week(query, column):
    date = get_date(query[column])
    one_week_ago = dt.date.today() - dt.timedelta(days=7)
    two_weeks_ago = one_week_ago - dt.timedelta(days=7)
    return query[date.between(one_week_ago, two_weeks_ago)]


def previous_month(query, column):
    date = get_date(query[column])
    one_month_ago = dt.date.today() - relativedelta(months=1)
    two_months_ago = one_month_ago - relativedelta(months=1)
    return query[date.between(one_month_ago, two_months_ago)]


def previous_year(query, column):
    date = get_date(query[column])
    one_year_ago = dt.date.today() - relativedelta(years=1)
    two_years_ago = one_year_ago - relativedelta(years=1)
    return query[date.between(one_year_ago, two_years_ago)]


def previous_last_week(query, column):
    date = get_date(query[column])
    year, week, _ = (dt.date.today() - dt.timedelta(days=14)).isocalendar()
    return query[(date.year() == year) & (date.isoweek() == week)]


def previous_last_n_days(query, column, days):
    date = get_date(query[column])
    end_day = dt.date.today() - dt.timedelta(days=days)
    n_days_ago = end_day - dt.timedelta(days=days)
    return query[date.between(n_days_ago, end_day)]


def previous_last_month(query, column):
    date = get_date(query[column])
    last_month = dt.date.today() - relativedelta(months=2)
    return query[(date.year() == last_month.year) & (date.month() == last_month.month)]


def previous_last_12_month(query, column):
    date = get_date(query[column])
    one_year_ago = dt.date.today() - relativedelta(months=12)
    two_years_ago = one_year_ago - relativedelta(months=12)
    return query[date.between(one_year_ago, two_years_ago)]


def previous_last_year(query, column):
    date = get_date(query[column])
    last_year = (dt.date.today() - relativedelta(years=2)).year
    return query[date.year() == last_year]


PREVIOUS_DATERANGE = {
    DateRange.ONEWEEKAGO: previous_week,
    DateRange.ONEMONTHAGO: previous_month,
    DateRange.ONEYEARAGO: previous_year,
    DateRange.LAST_WEEK: previous_last_week,
    DateRange.LAST_7: partial(previous_last_n_days, days=7),
    DateRange.LAST_14: partial(previous_last_n_days, days=14),
    DateRange.LAST_28: partial(previous_last_n_days, days=28),
    DateRange.LAST_30: partial(previous_last_n_days, days=30),
    DateRange.LAST_MONTH: previous_last_month,
    DateRange.LAST_90: partial(previous_last_n_days, days=90),
    DateRange.LAST_180: partial(previous_last_n_days, days=180),
    DateRange.LAST_12_MONTH: previous_last_12_month,
    DateRange.LAST_YEAR: previous_last_year,
}

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
    **DATETIME_FILTERS,
    Filter.Type.BOOL: filter_boolean,
}


def get_query_from_filter(query, filter: Filter, use_previous_period):
    column = filter.column
    predicate = (
        getattr(filter, PREDICATE_MAP[filter.type])
        if filter.type != Filter.Type.BOOL
        else None
    )
    func = PREVIOUS_DATERANGE.get(predicate) or FILTER_MAP[predicate or filter.type]
    value_str = "values" if predicate in ["isin", "notin"] else "value"
    value = getattr(filter, f"{filter.type.lower()}_{value_str}")
    func_params = signature(func).parameters
    if "value" not in func_params and "values" not in func_params:
        return func(query, column)
    return func(query, column, value)


def get_query_from_filters(query, filters: List[Filter], use_previous_period: False):
    return reduce(
        partial(get_query_from_filter, use_previous_period=use_previous_period),
        filters,
        query,
    )
