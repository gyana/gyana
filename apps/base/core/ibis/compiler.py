import ibis.expr.datatypes as dt
import ibis.expr.rules as rlz
from ibis.expr.operations import (
    Arg,
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
    TimestampValue,
    TimeValue,
)
from ibis_bigquery.compiler import BigQueryExprTranslator, _timestamp_units

compiles = BigQueryExprTranslator.compiles


class StartsWith(ValueOp):
    value = Arg(rlz.string)
    start_string = Arg(rlz.string)
    output_type = rlz.shape_like("value", dt.boolean)


def startswith(value, start_string):
    return StartsWith(value, start_string).to_expr()


class EndsWith(ValueOp):
    value = Arg(rlz.string)
    end_string = Arg(rlz.string)
    output_type = rlz.shape_like("value", dt.boolean)


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
    arg = Arg(rlz.column(rlz.any))

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
        left = Arg(data_type)
        right = Arg(data_type)
        unit = Arg(rlz.string)
        output_type = rlz.shape_like("left", dt.int64)

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
    value = Arg(rlz.string)
    json_path = Arg(rlz.string)
    output_type = rlz.shape_like("value", dt.string)


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
    arg = Arg(rlz.one_of([rlz.date, rlz.timestamp]))
    output_type = rlz.shape_like("arg", dt.int32)


def isoweek(arg):
    return ISOWeek(arg).to_expr()


DateValue.isoweek = isoweek
TimestampValue.isoweek = isoweek


@compiles(ISOWeek)
def _isoweek(t, expr):
    (arg,) = expr.op().args

    return f"EXTRACT(ISOWEEK from {t.translate(arg)})"


class DayOfWeek(ValueOp):
    arg = Arg(rlz.one_of([rlz.date, rlz.timestamp]))
    output_type = rlz.shape_like("arg", dt.int32)


def day_of_week(arg):
    return DayOfWeek(arg).to_expr()


DateValue.day_of_week = day_of_week
TimestampValue.day_of_week = day_of_week


@compiles(DayOfWeek)
def _day_of_week(t, expr):
    (arg,) = expr.op().args

    return f"EXTRACT(DAYOFWEEK FROM {t.translate(arg)})"


class ParseDate(ValueOp):
    value = Arg(rlz.string)
    format_ = Arg(rlz.string)
    output_type = rlz.shape_like("value", dt.date)


def parse_date(value, format_):
    return ParseDate(value, format_).to_expr()


StringValue.parse_date = parse_date


@compiles(ParseDate)
def _parse_date(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_DATE({t.translate(format_)}, {t.translate(value)})"


class ParseTime(ValueOp):
    value = Arg(rlz.string)
    format_ = Arg(rlz.string)
    output_type = rlz.shape_like("value", dt.time)


def parse_time(value, format_):
    return ParseTime(value, format_).to_expr()


StringValue.parse_time = parse_time


@compiles(ParseTime)
def _parse_time(t, expr):
    value, format_ = expr.op().args
    return f"PARSE_TIME({t.translate(format_)}, {t.translate(value)})"


class ParseDatetime(ValueOp):
    value = Arg(rlz.string)
    format_ = Arg(rlz.string)
    output_type = rlz.shape_like("value", dt.timestamp)


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
    date = Arg(rlz.date)
    days = Arg(rlz.integer)
    output_type = rlz.shape_like("args", dt.date)


def subtract_days(date, days):
    return SubtractDays(date, days).to_expr()


DateValue.subtract_days = subtract_days


@compiles(SubtractDays)
def _subtract_days(translator, expr):
    date, days = expr.op().args
    t_date = translator.translate(date)
    t_days = translator.translate(days)

    return f"DATE_SUB({t_date}, INTERVAL {t_days} DAY)"
