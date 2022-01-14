import datetime as dt
from functools import partial

from dateutil.relativedelta import relativedelta

from apps.filters.bigquery import (
    DATETIME_FILTERS,
    get_date,
    get_quarter,
    last_month,
    last_week,
    last_year,
    today,
    yesterday,
)
from apps.filters.models import DateRange

from .models import CustomChoice


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


def day_before_yesterday(query, column):
    date = get_date(query[column])
    yesterday_ = dt.date.today() - dt.timedelta(days=2)
    return query[date == yesterday_]


def previous_this_week_uptodate(query, column):
    date = get_date(query[column])
    today_last_week = dt.date.today() - dt.timedelta(days=7)
    start_of_week = today - dt.timedelta(days=today_last_week.weekday())
    return query[date.between(start_of_week, today_last_week)]


def previous_this_month_uptodate(query, column):
    date = get_date(query[column])
    today_last_month = dt.date.today() - relativedelta(month=1)
    return query[date.between(today_last_month.replace(day=1), today_last_month)]


def previous_this_quarter(query, column):
    date = get_date(query[column])
    today_last_quarter = dt.date.today() - relativedelta(months=3)
    quarter = get_quarter(today_last_quarter)
    return query[(date.year() == today_last_quarter.year) & (date.quarter() == quarter)]


def previous_this_quarter_uptodate(query, column):
    date = get_date(query[column])
    today_last_quarter = dt.date.today() - relativedelta(months=3)
    quarter = get_quarter(today_last_quarter)
    return query[
        date.between(
            dt.date(today_last_quarter.year, (quarter - 1) * 3 + 1, 1),
            today_last_quarter,
        )
    ]


def previous_last_quarter(query, column):
    date = get_date(query[column])
    today_previous_last_quarter = dt.date.today() - relativedelta(months=6)
    quarter = get_quarter(today_previous_last_quarter)
    return query[
        (date.year() == today_previous_last_quarter.year) & (date.quarter() == quarter)
    ]


def previous_this_year_up_todate(query, column):
    date = get_date(query[column])
    today_last_year = dt.date.today() - relativedelta(years=1)
    return query[(date.year() == today_last_year.year) & (date <= today_last_year)]


def previous_last_full_12_month(query, column):
    today_last_year = dt.date.today() - relativedelta(months=12)
    date = get_date(query[column])
    twelve_month_ago = (today_last_year - relativedelta(months=12)).replace(day=1)
    return query[date.between(twelve_month_ago, today_last_year)]


PREVIOUS_DATERANGE = {
    DateRange.TODAY: yesterday,
    DateRange.TOMORROW: today,
    DateRange.YESTERDAY: day_before_yesterday,
    DateRange.ONEWEEKAGO: previous_week,
    DateRange.ONEMONTHAGO: previous_month,
    DateRange.ONEYEARAGO: previous_year,
    DateRange.THIS_WEEK: last_week,
    DateRange.THIS_WEEK_UP_TO_DATE: previous_this_week_uptodate,
    DateRange.LAST_WEEK: previous_last_week,
    DateRange.LAST_7: partial(previous_last_n_days, days=7),
    DateRange.LAST_14: partial(previous_last_n_days, days=14),
    DateRange.LAST_28: partial(previous_last_n_days, days=28),
    DateRange.LAST_30: partial(previous_last_n_days, days=30),
    DateRange.THIS_MONTH: last_month,
    DateRange.THIS_MONTH_UP_TO_DATE: previous_this_month_uptodate,
    DateRange.LAST_MONTH: previous_last_month,
    DateRange.LAST_90: partial(previous_last_n_days, days=90),
    DateRange.THIS_QUARTER: previous_this_quarter,
    DateRange.THIS_QUARTER_UP_TO_DATE: previous_this_quarter_uptodate,
    DateRange.LAST_QUARTER: previous_last_quarter,
    DateRange.LAST_180: partial(previous_last_n_days, days=180),
    DateRange.THIS_YEAR: last_year,
    DateRange.THIS_YEAR_UP_TO_DATE: previous_this_year_up_todate,
    DateRange.LAST_12_MONTH: previous_last_12_month,
    DateRange.LAST_FULL_12_MONTH: previous_last_full_12_month,
    DateRange.LAST_YEAR: previous_last_year,
}


def slice_query(query, column, control, use_previous_period):
    if control.date_range != CustomChoice.CUSTOM:
        range_filter = (
            DATETIME_FILTERS[control.date_range]
            if not use_previous_period
            else PREVIOUS_DATERANGE[control.date_range]
        )
        return range_filter(query, column)

    if control.start:
        query = query[query[column] > control.start]

    if control.end:
        query = query[query[column] < control.end]

    return query
