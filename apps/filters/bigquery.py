import datetime as dt
import functools
from typing import List

from dateutil.relativedelta import relativedelta
from ibis.expr.types import TimestampValue

from apps.filters.models import PREDICATE_MAP, Filter


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


def isnull(query, column, value):
    return query[query[column].isnull()]


def notnull(query, column, value):
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


def islower(query, column, value):
    return query[query[column] == query[column].lower()]


def isupper(query, column, value):
    return query[query[column] == query[column].upper()]


def get_date(column):
    if isinstance(column, TimestampValue):
        return column.date()
    return column


def today(query, column, value):
    date = get_date(query[column])
    today = dt.date.today()
    return query[date == today]


def tomorrow(query, column, value):
    date = get_date(query[column])
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    return query[date == tomorrow]


def yesterday(query, column, value):
    date = get_date(query[column])
    yesterday_ = dt.date.today() - dt.timedelta(days=1)
    return query[date == yesterday_]


def one_week_ago(query, column, value):
    date = get_date(query[column])
    today = dt.date.today()
    one_week = today - dt.timedelta(days=7)
    return query[date.between(one_week, today)]


def one_month_ago(query, column, value):
    date = get_date(query[column])
    today = dt.date.today()
    one_month = today - relativedelta(months=1)
    return query[date.between(one_month, today)]


def one_year_ago(query, column, value):
    date = get_date(query[column])
    today = dt.date.today()
    one_year = today - relativedelta(years=1)
    return query[date.between(one_year, today)]


def filter_boolean(query, column, value):
    return query[query[column] == value]


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
    Filter.DatetimePredicate.TODAY: today,
    Filter.DatetimePredicate.TOMORROW: tomorrow,
    Filter.DatetimePredicate.YESTERDAY: yesterday,
    Filter.DatetimePredicate.ONEWEEKAGO: one_week_ago,
    Filter.DatetimePredicate.ONEMONTHAGO: one_month_ago,
    Filter.DatetimePredicate.ONEYEARAGO: one_year_ago,
    Filter.Type.BOOL: filter_boolean,
}


def get_query_from_filter(query, filter: Filter):
    column = filter.column
    predicate = (
        getattr(filter, PREDICATE_MAP[filter.type])
        if filter.type != Filter.Type.BOOL
        else None
    )
    func = FILTER_MAP[predicate or filter.type]
    value_str = "values" if predicate in ["isin", "notin"] else "value"
    value = getattr(filter, f"{filter.type.lower()}_{value_str}")

    return func(query, column, value)


def get_query_from_filters(query, filters: List[Filter]):
    return functools.reduce(get_query_from_filter, filters, query)
