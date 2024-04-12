import ibis.expr.datatypes as dt
import ibis.expr.rules as rlz
from ibis.backends.bigquery.compiler import BigQueryExprTranslator
from ibis.expr.operations import (
    Reduction,
    Value,
)
from ibis.expr.types import (
    Column,
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
