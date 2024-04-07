import ibis.expr.datatypes as dt
import ibis.expr.rules as rlz
from ibis.backends.bigquery.compiler import BigQueryExprTranslator
from ibis.expr.operations import (
    Constant,
    Reduction,
    Value,
)
from ibis.expr.types import (
    Column,
    DateScalar,
    StructValue,
    TimestampValue,
)

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
