import datetime as dt
from functools import partial

from dateutil.relativedelta import relativedelta
from ibis.expr.types import TimestampValue

from apps.filters.models import DateRange

from .models import CustomChoice


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


def filter_boolean(query, column, value):
    return query[query[column] == value]


def previous_week(query, column):
    date = get_date(query[column])
    one_week_ago = dt.date.today() - dt.timedelta(days=7)
    two_weeks_ago = one_week_ago - dt.timedelta(days=7)
    return query[date.between(two_weeks_ago, one_week_ago)]


def previous_month(query, column):
    date = get_date(query[column])
    today = dt.date.today()
    one_month_ago = today - relativedelta(months=1)
    two_months_ago = today - relativedelta(months=2)
    return query[date.between(two_months_ago, one_month_ago)]


def previous_year(query, column):
    date = get_date(query[column])
    one_year_ago = dt.date.today() - relativedelta(years=1)
    two_years_ago = one_year_ago - relativedelta(years=1)
    return query[date.between(two_years_ago, one_year_ago)]


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
    return query[date.between(two_years_ago, one_year_ago)]


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
    start_of_week = today_last_week - dt.timedelta(days=today_last_week.weekday())
    return query[date.between(start_of_week, today_last_week)]


def previous_this_month_uptodate(query, column):
    date = get_date(query[column])
    today_last_month = dt.date.today() - relativedelta(months=1)
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


DATETIME_FILTERS = {
    DateRange.TODAY: {
        "function": today,
        "previous_function": yesterday,
        "previous_label": "yesterday",
    },
    DateRange.TOMORROW: {
        "function": tomorrow,
        "previous_function": today,
        "previous_label": "today",
    },
    DateRange.YESTERDAY: {
        "function": yesterday,
        "previous_function": day_before_yesterday,
        "previous_label": "the day before yesterday",
    },
    DateRange.ONEWEEKAGO: {
        "function": one_week_ago,
        "previous_function": previous_week,
        "previous_label": "two weeks ago",
    },
    DateRange.ONEMONTHAGO: {
        "function": one_month_ago,
        "previous_function": previous_month,
        "previous_label": "two months ago",
    },
    DateRange.ONEYEARAGO: {
        "function": one_year_ago,
        "previous_function": previous_year,
        "previous_label": "two years ago",
    },
    DateRange.THIS_WEEK: {
        "function": this_week,
        "previous_function": last_week,
        "previous_label": "previous week",
    },
    DateRange.THIS_WEEK_UP_TO_DATE: {
        "function": this_week_up_todate,
        "previous_function": previous_this_week_uptodate,
        "previous_label": "previous week",
    },
    DateRange.LAST_WEEK: {
        "function": last_week,
        "previous_function": previous_last_week,
        "previous_label": "previous week",
    },
    DateRange.LAST_7: {
        "function": partial(last_n_days, days=7),
        "previous_function": partial(previous_last_n_days, days=7),
        "previous_label": "previous 7 days",
    },
    DateRange.LAST_14: {
        "function": partial(last_n_days, days=14),
        "previous_function": partial(previous_last_n_days, days=14),
        "previous_label": "previous 14 days",
    },
    DateRange.LAST_28: {
        "function": partial(last_n_days, days=28),
        "previous_function": partial(previous_last_n_days, days=28),
        "previous_label": "previous 28 days",
    },
    DateRange.LAST_30: {
        "function": partial(last_n_days, days=30),
        "previous_function": partial(previous_last_n_days, days=30),
        "previous_label": "previous 30 days",
    },
    DateRange.THIS_MONTH: {
        "function": this_month,
        "previous_function": last_month,
        "previous_label": "previous month",
    },
    DateRange.THIS_MONTH_UP_TO_DATE: {
        "function": this_month_up_to_date,
        "previous_function": previous_this_month_uptodate,
        "previous_label": "previous month",
    },
    DateRange.LAST_MONTH: {
        "function": last_month,
        "previous_function": previous_last_month,
        "previous_label": "previous month",
    },
    DateRange.LAST_90: {
        "function": partial(last_n_days, days=90),
        "previous_function": partial(previous_last_n_days, days=90),
        "previous_label": "previous 90 days",
    },
    DateRange.THIS_QUARTER: {
        "function": this_quarter,
        "previous_function": previous_this_quarter,
        "previous_label": "previous quarter",
    },
    DateRange.THIS_QUARTER_UP_TO_DATE: {
        "function": this_quarter_up_to_date,
        "previous_function": previous_this_quarter_uptodate,
        "previous_label": "previous quarter",
    },
    DateRange.LAST_QUARTER: {
        "function": last_quarter,
        "previous_function": previous_last_quarter,
        "previous_label": "previous quarter",
    },
    DateRange.LAST_180: {
        "function": partial(last_n_days, days=180),
        "previous_function": partial(previous_last_n_days, days=180),
        "previous_label": "previous 180 days",
    },
    DateRange.THIS_YEAR: {
        "function": this_year,
        "previous_function": last_year,
        "previous_label": "previous year",
    },
    DateRange.THIS_YEAR_UP_TO_DATE: {
        "function": this_year_up_todate,
        "previous_function": previous_this_year_up_todate,
        "previous_label": "previous year",
    },
    DateRange.LAST_12_MONTH: {
        "function": last_12_month,
        "previous_function": previous_last_12_month,
        "previous_label": "previous 12 months",
    },
    DateRange.LAST_FULL_12_MONTH: {
        "function": last_full_12_month,
        "previous_function": previous_last_full_12_month,
        "previous_label": "previous 12 months",
    },
    DateRange.LAST_YEAR: {
        "function": last_year,
        "previous_function": previous_last_year,
        "previous_label": "previous year",
    },
}


def slice_query(query, column, control, use_previous_period):
    if control.date_range != CustomChoice.CUSTOM:
        func = DATETIME_FILTERS[control.date_range]
        range_filter = (
            func["function"] if not use_previous_period else func["previous_function"]
        )
        return range_filter(query, column)

    if control.start:
        query = query[query[column] > control.start]

    if control.end:
        query = query[query[column] < control.end]

    return query
