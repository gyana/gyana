import datetime as dt
from functools import partial

from apps.filters import bigquery as filters

from .models import DateSlicer

Range = DateSlicer.Range


def this_week(query, column):
    date = filters.get_date(query[column])
    year, week, _ = dt.date.today().isocalendar()
    return query[date.year() == year & date.isoweek() == week]


def last_week(query, column):
    date = filters.get_date(query[column])
    year, week, _ = dt.date.today().isocalendar()
    # If this week is first of this year we are interested in the last week of last year
    if week == 1:
        year -= 1
        week = 52
    else:
        week -= 1
    return query[(date.year() == year) & (date.isoweek() == week)]


def last_n_days(query, column, days):
    date = filters.get_date(query[column])
    today = dt.date.today()
    n_days_ago = today - dt.timedelta(days=days)
    return query[date.between(n_days_ago, today)]


def this_month(query, column):
    date = filters.get_date(query[column])
    today = dt.date.today()
    return query[(date.year() == today.year) & (date.month() == today.month)]


def last_month(query, column):
    date = filters.get_date(query[column])
    last_month = dt.today() - dt.timedelta(months=1)
    return query[(date.year() == last_month.year) & (date.month() == last_month.month)]


def this_quarter(query, column):
    pass


def last_quarter(query, column):
    pass


def this_year(query, column):
    date = filters.get_date(query[column])
    today = dt.date.today()
    return query[(date.year() == today.year) & (date <= today)]


def last_12_month(query, column):
    date = filters.get_date(query[column])
    today = dt.date.today()
    twelve_month_ago = today - dt.timedelta(months=12)
    return query[date.between(today, twelve_month_ago)]


def last_year(query, column):
    date = filters.get_date(query[column])
    last_year = (dt.date.today() - dt.timedelta(years=1)).year
    return query[date.year() == last_year]


RANGE_FUNCTIONS = {
    Range.TODAY: partial(filters.today, value=None),
    Range.YESTERDAY: partial(filters.yesterday, value=None),
    Range.THIS_WEEK: this_week,
    Range.LAST_WEEK: last_week,
    Range.LAST_7: partial(last_n_days, days=7),
    Range.LAST_14: partial(last_n_days, days=14),
    Range.LAST_28: partial(last_n_days, days=28),
    Range.LAST_30: partial(last_n_days, days=30),
    Range.THIS_MONTH: this_month,
    Range.LAST_MONTH: last_month,
    Range.LAST_90: partial(last_n_days, days=90),
    Range.THIS_QUARTER: this_quarter,
    Range.LAST_QUARTER: last_quarter,
    Range.LAST_180: partial(last_n_days, days=180),
    Range.THIS_YEAR: this_year,
    Range.LAST_12_MONTH: last_12_month,
    Range.LAST_YEAR: last_year,
}


def slice_query(query, column, date_slicer):
    if date_slicer.date_range != DateSlicer.Range.CUSTOM:
        range_filter = RANGE_FUNCTIONS[date_slicer.date_range]
        return range_filter(query, column)

    if date_slicer.start:
        query = query[query[column] > date_slicer.start]

    if date_slicer.end:
        query = query[query[column] < date_slicer.end]

    return query
