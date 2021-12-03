import ibis.expr.datatypes as dt
import ibis.expr.rules as rlz
from ibis.expr.operations import (
    Arg,
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
from ibis_bigquery import BigQueryExprTranslator
from ibis_bigquery.compiler import _timestamp_units

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
        output_type = rlz.shape_like("left", dt.float64)

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

    return f"ISOWEEK {t.translate(arg)}"
