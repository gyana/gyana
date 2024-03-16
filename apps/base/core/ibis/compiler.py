import ibis.expr.datatypes as dt
import ibis.expr.rules as rlz
from ibis.backends.bigquery.compiler import BigQueryExprTranslator
from ibis.expr.operations import (
    Constant,
    DateDiff,
    Reduction,
    TimeDiff,
    TimestampDiff,
    Value,
)
from ibis.expr.types import (
    Column,
    DateScalar,
    DateValue,
    StringValue,
    StructValue,
    TimestampValue,
    TimeValue,
)

_date_units = {
    "Y": "YEAR",
    "Q": "QUARTER",
    "W": "WEEK(MONDAY)",
    "M": "MONTH",
    "D": "DAY",
}


_timestamp_units = {
    "us": "MICROSECOND",
    "ms": "MILLISECOND",
    "s": "SECOND",
    "m": "MINUTE",
    "h": "HOUR",
}
_timestamp_units.update(_date_units)

# Do not place compile functions and classes in a function as local variables
# this will mess with cacheops and lead to cant pickle local object error

compiles = BigQueryExprTranslator.compiles


class AnyValue(Reduction):
    arg: Value

    dtype = rlz.dtype_like("arg")


def any_value(arg):
    return AnyValue(arg).to_expr()


Column.any_value = any_value


@compiles(AnyValue)
def _any_value(t, expr):
    (arg,) = expr.op().args

    return f"ANY_VALUE({t.translate(arg)})"


class TimestampDifference(Value):
    left: Value[dt.Timestamp]
    right: Value[dt.Timestamp]
    unit: Value[dt.String]

    shape = rlz.shape_like("left")
    dtype = dt.int64


def timestamp_difference(left, right, unit):
    return TimestampDifference(left, right, unit).to_expr()


TimestampValue.timestamp_diff = timestamp_difference


@compiles(TimestampDifference)
def _timestamp_difference(translator, expr):
    left, right, unit = expr.op().args
    t_left = translator.translate(left)
    t_right = translator.translate(right)
    t_unit = _timestamp_units[translator.translate(unit).replace("'", "")]
    return f"TIMESTAMP_DIFF({t_left}, {t_right}, {t_unit})"


class DateDifference(Value):
    left: Value[dt.Date]
    right: Value[dt.Date]
    unit: Value[dt.String]

    shape = rlz.shape_like("left")
    dtype = dt.int64


def date_difference(left, right, unit):
    return DateDifference(left, right, unit).to_expr()


DateValue.timestamp_diff = date_difference


@compiles(DateDifference)
def _date_difference(translator, expr):
    left, right, unit = expr.op().args
    t_left = translator.translate(left)
    t_right = translator.translate(right)
    t_unit = _timestamp_units[translator.translate(unit).replace("'", "")]
    return f"DATE_DIFF({t_left}, {t_right}, {t_unit})"


class TimeDifference(Value):
    left: Value[dt.Time]
    right: Value[dt.Time]
    unit: Value[dt.String]
    shape = rlz.shape_like("left")
    dtype = dt.int64


def time_difference(left, right, unit):
    return TimeDifference(left, right, unit).to_expr()


TimeValue.timestamp_diff = time_difference


@compiles(TimeDifference)
def _time_difference(translator, expr):
    left, right, unit = expr.op().args
    t_left = translator.translate(left)
    t_right = translator.translate(right)
    t_unit = _timestamp_units[translator.translate(unit).replace("'", "")]
    return f"TIME_DIFF({t_left}, {t_right}, {t_unit})"


def _compiles_timestamp_diff_op(op, bq_func, unit):
    def diff(translator, expr):
        left, right = expr.op().args
        t_left = translator.translate(left)
        t_right = translator.translate(right)

        return f"{bq_func}({t_left}, {t_right}, {unit})"

    return compiles(op)(diff)


_compiles_timestamp_diff_op(TimestampDiff, "TIMESTAMP_DIFF", "SECOND")
_compiles_timestamp_diff_op(TimeDiff, "TIME_DIFF", "SECOND")
_compiles_timestamp_diff_op(DateDiff, "DATE_DIFF", "DAY")


class JSONExtract(Value):
    value: Value[dt.String]
    json_path: Value[dt.String]
    shape = rlz.shape_like("value")
    dtype = dt.string


def json_extract(value, json_path):
    return JSONExtract(value, json_path).to_expr()


StringValue.json_extract = json_extract


@compiles(JSONExtract)
def _json_extract(t, expr):
    value, json_path = expr.op().args
    t_value = t.translate(value)
    t_json_path = t.translate(json_path)

    return f"JSON_QUERY({t_value}, {t_json_path})"


class ISOWeek(Value):
    arg: Value[dt.Date | dt.Timestamp]

    shape = rlz.shape_like("arg")
    dtype = dt.int32


def isoweek(arg):
    return ISOWeek(arg).to_expr()


DateValue.isoweek = isoweek
TimestampValue.isoweek = isoweek


@compiles(ISOWeek)
def _isoweek(t, expr):
    (arg,) = expr.op().args

    return f"EXTRACT(ISOWEEK from {t.translate(arg)})"


class DayOfWeek(Value):
    arg: Value[dt.Date | dt.Timestamp]

    shape = rlz.shape_like("arg")
    dtype = dt.int32


def day_of_week(arg):
    return DayOfWeek(arg).to_expr()


DateValue.day_of_week = day_of_week
TimestampValue.day_of_week = day_of_week


@compiles(DayOfWeek)
def _day_of_week(t, expr):
    (arg,) = expr.op().args

    return f"EXTRACT(DAYOFWEEK FROM {t.translate(arg)})"


class ParseDate(Value):
    value: Value[dt.String]
    format_: Value[dt.String]

    shape = rlz.shape_like("value")
    dtype = dt.date


def parse_date(value, format_):
    return ParseDate(value, format_).to_expr()


StringValue.parse_date = parse_date


@compiles(ParseDate)
def _parse_date(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_DATE({t.translate(format_)}, {t.translate(value)})"


class ParseTime(Value):
    value: Value[dt.String]
    format_: Value[dt.String]
    shape = rlz.shape_like("value")

    dtype = dt.time


def parse_time(value, format_):
    return ParseTime(value, format_).to_expr()


StringValue.parse_time = parse_time


@compiles(ParseTime)
def _parse_time(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_TIME({t.translate(format_)}, {t.translate(value)})"


class ParseDatetime(Value):
    value: Value[dt.String]
    format_: Value[dt.String]

    shape = rlz.shape_like("value")
    dtype = dt.timestamp


def parse_datetime(value, format_):
    return ParseDatetime(value, format_).to_expr()


StringValue.parse_datetime = parse_datetime


@compiles(ParseDatetime)
def _parse_datetime(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_TIMESTAMP({t.translate(format_)}, {t.translate(value)})"


# TODO: Can be removed once https://github.com/ibis-project/ibis/pull/8664/files
# is merged
class Today(Constant):
    dtype = dt.date


def today() -> DateScalar:
    """
    Compute today's date

    Returns
    -------
    today : Date scalar
    """
    return Today().to_expr()


@compiles(Today)
def _today(t, expr):
    return "CURRENT_DATE()"


# @ibis.udf.scalar.builtin(name="current_date")
# def today() -> datetime.date: ...


# Unfortunately, ibis INTERVAL doesnt except variables
class SubtractDays(Value):
    date: Value[dt.Date]
    days: Value[dt.Integer]

    shape = rlz.shape_like("args")
    dtype = dt.date


def subtract_days(date, days):
    return SubtractDays(date, days).to_expr()


DateValue.subtract_days = subtract_days


@compiles(SubtractDays)
def _subtract_days(translator, expr):
    date, days = expr.op().args
    t_date = translator.translate(date)
    t_days = translator.translate(days)

    return f"DATE_SUB({t_date}, INTERVAL {t_days} DAY)"


class Date(Value):
    date: Value[dt.Date]

    shape = rlz.shape_like("date")
    dtype = dt.date


def date(d):
    return Date(d).to_expr()


DateValue.date = date


@compiles(Date)
def _date(t, expr):
    d = expr.op().args[0]
    return t.translate(d)


class ToJsonString(Value):
    struct: Value[dt.Struct]

    shape = rlz.shape_like("struct")
    dtype = dt.string


def to_json_string(struct):
    return ToJsonString(struct).to_expr()


StructValue.to_json_string = to_json_string


@compiles(ToJsonString)
def _to_json_string(t, expr):
    struct = t.translate(expr.op().args[0])

    return f"TO_JSON_STRING({struct})"


# Converts bigquery DATETIME to TIMESTAMP in UTC timezone
class ToTimestamp(Value):
    datetime: Value[dt.Timestamp]
    timezone: Value[dt.String]

    shape = rlz.shape_like("datetime")
    dtype = dt.timestamp


def to_timestamp(d):
    return ToTimestamp(d).to_expr()


TimestampValue.to_timestamp = to_timestamp


@compiles(ToTimestamp)
def _to_timestamp(t, expr):
    d = expr.op().args[0]
    return f"TIMESTAMP({t.translate(d)})"


class ToTimezone(Value):
    datetime: Value[dt.Timestamp]
    timezone: Value[dt.String]

    shape = rlz.shape_like("datetime")
    dtype = dt.timestamp


def to_timezone(d, tz):
    return ToTimezone(d, tz).to_expr()


TimestampValue.to_timezone = to_timezone


@compiles(ToTimezone)
def _to_timezone(t, expr):
    d, tz = expr.op().args

    return f"TIMESTAMP(DATETIME({t.translate(d)}, {t.translate(tz)}))"
