import datetime as dt
from functools import partial

from apps.filters import bigquery as filters

from .models import DateSlicer

Range = DateSlicer.Range


def this_week(query, column):
    date = filters.get_date(query[column])
    year, week, _ = dt.date.today().isocalendar()
    return query[date.year() == year & date.isoweek() == week]


def this_year(query, column):
    date = filters.get_date(query[column])
    today = dt.date.today()
    return query[date.year() == today.year & date <= today]


RANGE_FUNCTIONS = {
    Range.TODAY: partial(filters.today, value=None),
    Range.YESTERDAY: partial(filters.yesterday, value=None),
    Range.LAST_7: partial(filters.one_week_ago, value=None),
    Range.THIS_YEAR: this_year,
}


def slice_query(query, column, date_slicer):
    if date_slicer.date_range:
        range_filter = RANGE_FUNCTIONS[date_slicer.date_range]
        return range_filter(query, column)

    if date_slicer.start:
        query = query[query[column] > date_slicer.start]

    if date_slicer.end:
        query = query[query[column] < date_slicer.end]

    return query
