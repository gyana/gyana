import ibis.expr.datatypes as dt
import ibis.expr.rules as rlz
from ibis.expr.operations import (
    Constant,
    DateDiff,
    Reduction,
    TimeDiff,
    TimestampDiff,
    ValueOp,
)
from ibis.expr.types import (
    ColumnExpr,
    DateValue,
    StringValue,
    StructValue,
    TimestampValue,
    TimeValue,
)
from ibis_bigquery.compiler import BigQueryExprTranslator, _timestamp_units

compiles = BigQueryExprTranslator.compiles


class StartsWith(ValueOp):
    value = rlz.string
    start_string = rlz.string
    output_dtype = rlz.dtype_like("value")
    output_shape = rlz.shape_like("value")


def startswith(value, start_string):
    return StartsWith(value, start_string).to_expr()


class EndsWith(ValueOp):
    value = rlz.string
    end_string = rlz.string
    output_dtype = rlz.dtype_like("value")
    output_shape = rlz.shape_like("value")


def endswith(value, start_string):
    return EndsWith(value, start_string).to_expr()


StringValue.startswith = startswith
StringValue.endswith = endswith


@compiles(StartsWith)
def _startswith(t, expr):
    # pull out the arguments to the expression
    value, start_string = expr.op().args
    # compile the argument
    t_value = t.translate(value)
    t_start = t.translate(start_string)
    # return a SQL expression that calls the BigQuery STARTS_WITH function
    return f"STARTS_WITH({t_value}, {t_start})"


@compiles(EndsWith)
def _endswith(t, expr):
    # pull out the arguments to the expression
    value, start_string = expr.op().args
    # compile the argument
    t_value = t.translate(value)
    t_start = t.translate(start_string)
    # return a SQL expression that calls the BigQuery STARTS_WITH function
    return f"ENDS_WITH({t_value}, {t_start})"


class AnyValue(Reduction):
    arg = rlz.column(rlz.any)

    def output_type(self):
        return self.arg.type().scalar_type()


def any_value(arg):
    return AnyValue(arg).to_expr()


ColumnExpr.any_value = any_value


@compiles(AnyValue)
def _any_value(t, expr):
    (arg,) = expr.op().args

    return f"ANY_VALUE({t.translate(arg)})"


def _add_timestamp_diff_with_unit(value_class, bq_func, data_type):
    class Difference(ValueOp):
        left = data_type
        right = data_type
        unit = rlz.string
        output_type = rlz.shape_like("left")

    def difference(left, right, unit):
        return Difference(left, right, unit).to_expr()

    value_class.timestamp_diff = difference

    def _difference(translator, expr):
        left, right, unit = expr.op().args
        t_left = translator.translate(left)
        t_right = translator.translate(right)
        t_unit = _timestamp_units[translator.translate(unit).replace("'", "")]
        return f"{bq_func}({t_left}, {t_right}, {t_unit})"

    return compiles(Difference)(_difference)


_add_timestamp_diff_with_unit(TimestampValue, "TIMESTAMP_DIFF", rlz.timestamp)
_add_timestamp_diff_with_unit(DateValue, "DATE_DIFF", rlz.date)
_add_timestamp_diff_with_unit(TimeValue, "TIME_DIFF", rlz.time)


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


class JSONExtract(ValueOp):
    value = rlz.string
    json_path = rlz.string
    output_type = rlz.shape_like("value")


def json_extract(value, json_path):
    return JSONExtract(value, json_path).to_expr()


StringValue.json_extract = json_extract


@compiles(JSONExtract)
def _json_extract(t, expr):
    value, json_path = expr.op().args
    t_value = t.translate(value)
    t_json_path = t.translate(json_path)

    return f"JSON_QUERY({t_value}, {t_json_path})"


class ISOWeek(ValueOp):
    arg = rlz.one_of([rlz.date, rlz.timestamp])
    output_type = rlz.shape_like("arg")


def isoweek(arg):
    return ISOWeek(arg).to_expr()


DateValue.isoweek = isoweek
TimestampValue.isoweek = isoweek


@compiles(ISOWeek)
def _isoweek(t, expr):
    (arg,) = expr.op().args

    return f"EXTRACT(ISOWEEK from {t.translate(arg)})"


class DayOfWeek(ValueOp):
    arg = rlz.one_of([rlz.date, rlz.timestamp])
    output_type = rlz.shape_like("arg")


def day_of_week(arg):
    return DayOfWeek(arg).to_expr()


DateValue.day_of_week = day_of_week
TimestampValue.day_of_week = day_of_week


@compiles(DayOfWeek)
def _day_of_week(t, expr):
    (arg,) = expr.op().args

    return f"EXTRACT(DAYOFWEEK FROM {t.translate(arg)})"


class ParseDate(ValueOp):
    value = rlz.string
    format_ = rlz.string
    output_type = rlz.shape_like("value")


def parse_date(value, format_):
    return ParseDate(value, format_).to_expr()


StringValue.parse_date = parse_date


@compiles(ParseDate)
def _parse_date(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_DATE({t.translate(format_)}, {t.translate(value)})"


class ParseTime(ValueOp):
    value = rlz.string
    format_ = rlz.string
    output_type = rlz.shape_like("value")


def parse_time(value, format_):
    return ParseTime(value, format_).to_expr()


StringValue.parse_time = parse_time


@compiles(ParseTime)
def _parse_time(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_TIME({t.translate(format_)}, {t.translate(value)})"


class ParseDatetime(ValueOp):
    value = rlz.string
    format_ = rlz.string
    output_type = rlz.shape_like("value")


def parse_datetime(value, format_):
    return ParseDatetime(value, format_).to_expr()


StringValue.parse_datetime = parse_datetime


@compiles(ParseDatetime)
def _parse_datetime(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_TIMESTAMP({t.translate(format_)}, {t.translate(value)})"


class Today(Constant):
    def output_type(self):
        return dt.date.scalar_type()


def today():
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


# Unfortunately, ibis INTERVAL doesnt except variables
class SubtractDays(ValueOp):
    date = rlz.date
    days = rlz.integer
    output_shape = rlz.shape_like("args")
    output_type = rlz.dtype_like("args")


def subtract_days(date, days):
    return SubtractDays(date, days).to_expr()


DateValue.subtract_days = subtract_days


@compiles(SubtractDays)
def _subtract_days(translator, expr):
    date, days = expr.op().args
    t_date = translator.translate(date)
    t_days = translator.translate(days)

    return f"DATE_SUB({t_date}, INTERVAL {t_days} DAY)"


class Date(ValueOp):
    date = rlz.date
    output_shape = rlz.shape_like("date")
    output_dtype = rlz.dtype_like("date")


def date(d):
    return Date(d).to_expr()


DateValue.date = date


@compiles(Date)
def _date(t, expr):
    d = expr.op().args[0]
    return t.translate(d)


class ToJsonString(ValueOp):
    struct = rlz.struct
    output_type = rlz.shape_like("struct")


def to_json_string(struct):
    return ToJsonString(struct).to_expr()


StructValue.to_json_string = to_json_string


@compiles(ToJsonString)
def _to_json_string(t, expr):
    struct = t.translate(expr.op().args[0])

    return f"TO_JSON_STRING({struct})"


# Converts bigquery DATETIME to TIMESTAMP in UTC timezone
class ToTimesamp(ValueOp):
    datetime = rlz.timestamp
    output_type = rlz.shape_like("datetime")


def to_timestamp(d):
    return ToTimesamp(d).to_expr()


TimestampValue.to_timestamp = to_timestamp


@compiles(ToTimesamp)
def _to_timestamp(t, expr):
    d = expr.op().args[0]
    return f"TIMESTAMP({t.translate(d)})"


class ToTimezone(ValueOp):
    datetime = rlz.timestamp
    timezone = rlz.string
    output_type = rlz.shape_like("datetime")


def to_timezone(d, tz):
    return ToTimezone(d, tz).to_expr()


TimestampValue.to_timezone = to_timezone


@compiles(ToTimezone)
def _to_timezone(t, expr):
    d, tz = expr.op().args

    return f"TIMESTAMP(DATETIME({t.translate(d)}, {t.translate(tz)}))"
