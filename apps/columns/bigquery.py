from dataclasses import dataclass

from lark import Lark

from apps.columns.transformer import TreeToIbis

from .types import TYPES

parser = Lark.open("formula.lark", rel_to=__file__, start="formula")


@dataclass
class Operation:
    label: str
    arguments: int = 0
    value_field: str = None


CommonOperations = {
    "isnull": Operation("is empty"),
    "notnull": Operation("is not empty"),
}


StringOperations = {
    "fillna": Operation("fill empty values", 1, "string_value"),
    "lower": Operation("to lowercase"),
    "upper": Operation("to uppercase"),
    "length": Operation("length"),
    "reverse": Operation("reverse"),
    "strip": Operation("strip"),
    "lstrip": Operation("lstrip"),
    "rstrip": Operation("rstrip"),
    "like": Operation("like", 1, "string_value"),
    "contains": Operation("contains", 1, "string_value"),
    # TODO: write IBIS implementation and test
    # "left": Operation("left", 1, "integer_value"),
    # "right": Operation("right", 1, "integer_value"),
    # "repeat": Operation("repeat", 1, "integer_value"),
}

NumericOperations = {
    "cummax": Operation("cummax"),
    "cummin": Operation("cummin"),
    "abs": Operation("absolute value"),
    "sqrt": Operation("square root"),
    "ceil": Operation("ceiling"),
    "floor": Operation("floor"),
    "ln": Operation("ln"),
    "log2": Operation("log2"),
    "log10": Operation("log10"),
    "log": Operation("log", 1, "float_value"),
    "exp": Operation("exponent"),
    "add": Operation("add", 1, "float_value"),
    "sub": Operation("subtract", 1, "float_value"),
    "mul": Operation("multiply", 1, "float_value"),
    "div": Operation("divide", 1, "float_value"),
}

DateOperations = {
    "year": Operation("year"),
    "month": Operation("month"),
    "day": Operation("day"),
}

TimeOperations = {
    "hour": Operation("hour"),
    "minute": Operation("minute"),
    "second": Operation("second"),
    "millisecond": Operation("millisecond"),
}

DatetimeOperations = {
    "epoch_seconds": Operation("epoch seconds"),
    "time": Operation("time"),
    "date": Operation("date"),
}

AllOperations = {
    **CommonOperations,
    **NumericOperations,
    **StringOperations,
    **DateOperations,
    **TimeOperations,
    **DatetimeOperations,
}


def compile_function(query, edit):
    func = getattr(query[edit.column], edit.function)
    if value_field := AllOperations[edit.function].value_field:
        arg = getattr(edit, value_field)
        return func(arg)
    return func()


def compile_formula(query, formula):
    tree = parser.parse(formula)

    return TreeToIbis(query).transform(tree)


def convert_column(query, convert_column):
    type_ = TYPES[convert_column.target_type]
    return query[convert_column.column].cast(type_)


def resolve_colname(colname, computation, column_names):
    """If a column is aggregated over more than once
    Generate a new column as combination of computation and column_name"""
    if column_names.count(colname) > 1:
        return f"{computation}_{colname}"
    return colname


def get_aggregate_expr(query, colname, computation, column_names):
    """Creates an aggregation"""
    column = getattr(query, colname)

    colname = resolve_colname(colname, computation, column_names)
    return getattr(column, computation)().name(colname)


def aggregate_columns(query, instance):
    """Aggregates over multiple aggregations and resolves name conflicts"""
    groups = [col.column for col in instance.columns.all()]
    aggregations = instance.aggregations.all()
    column_names = [agg.column for agg in aggregations]
    aggregations = [
        get_aggregate_expr(query, agg.column, agg.function, column_names)
        for agg in instance.aggregations.all()
    ]
    if not groups and not aggregations:
        # query.count() returns a scalar
        # use aggregate to return TableExpr
        return query.aggregate(query.count())
    if groups:
        query = query.group_by(groups)
    if aggregations:
        return query.aggregate(aggregations)
    return query.count()
