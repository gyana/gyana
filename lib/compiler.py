import ibis.expr.rules as rlz
from ibis.expr.operations import Arg, ValueOp
from ibis.expr.types import StringValue
from ibis_bigquery import BigQueryExprTranslator

compiles = BigQueryExprTranslator.compiles


class StartsWith(ValueOp):
    value = Arg(rlz.string)
    start_string = Arg(rlz.string)
    output_type = rlz.shape_like("value", "bool")


def startswith(value, start_string):
    return StartsWith(value, start_string).to_expr()


class EndsWith(ValueOp):
    value = Arg(rlz.string)
    end_string = Arg(rlz.string)
    output_type = rlz.shape_like("value", "bool")


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
