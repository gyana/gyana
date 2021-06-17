from dataclasses import dataclass

from apps.filters.bigquery import create_filter_query
from lib.clients import ibis_client
from lib.formulas import to_ibis


def get_input_query(node):
    conn = ibis_client()
    # The input can have no selected integration
    return (
        conn.table(node.input_table.bq_table, database=node.input_table.bq_dataset)
        if node.input_table
        else None
    )


def get_output_query(node):
    return node.parents.first().get_query()


def get_select_query(node):
    parent_query = node.parents.first().get_query()
    return parent_query.projection([col.column for col in node.columns.all()] or [])


def get_duplicate_names(left, right):
    left_names = {name for name in left.schema()}
    right_names = {name for name in right.schema()}
    return left_names & right_names


def rename_duplicates(left, right, left_col, right_col):
    duplicates = get_duplicate_names(left, right)
    left = left.relabel({d: f"{d}_1" for d in duplicates})
    right = right.relabel({d: f"{d}_2" for d in duplicates})
    left_col = f"{left_col}_1" if left_col in duplicates else left_col
    right_col = f"{right_col}_2" if right_col in duplicates else right_col

    return left, right, left_col, right_col


def get_join_query(node):
    left = node.parents.first().get_query()
    right = node.parents.last().get_query()

    # Adding 1/2 to left/right if the column exists in both tables
    left, right, left_col, right_col = rename_duplicates(
        left, right, node.join_left, node.join_right
    )
    how = node.join_how
    if how == "inner":
        to_join = left.inner_join
    elif how == "outer":
        to_join = left.outer_join
    elif how == "left":
        to_join = left.left_join
    elif how == "right":
        to_join = left.right_join
    else:
        raise NotImplemented(f"Method {how} doesn't exist.")

    return to_join(right, left[left_col] == right[right_col]).materialize()


def aggregate(query, colname, computation):
    column = getattr(query, colname)
    return getattr(column, computation)().name(colname)


def get_aggregation_query(node):
    query = node.parents.first().get_query()
    groups = node.columns.all()
    aggregations = [
        aggregate(query, agg.column, agg.function) for agg in node.aggregations.all()
    ]
    if groups:
        query = query.group_by([g.column for g in groups])
    if aggregations:
        return query.aggregate(aggregations)
    return query.size()


def get_union_query(node):
    parents = node.parents.all()
    query = parents[0].get_query()
    colnames = query.schema()
    for parent in parents[1:]:
        query = query.union(parent.get_query(), distinct=node.union_distinct)
    # Need to `select *` so we can operate on the query
    return query.projection(colnames)


def get_sort_query(node):
    query = node.parents.first().get_query()
    sort_columns = [
        (getattr(query, s.column), s.ascending) for s in node.sort_columns.all()
    ]
    return query.sort_by(sort_columns)


def get_limit_query(node):
    query = node.parents.first().get_query()
    # Need to project again to make sure limit isn't overwritten
    return query.limit(node.limit_limit, offset=node.limit_offset or 0).projection(
        query.schema()
    )


def bigquery(node):
    return create_filter_query(node.parents.first().get_query(), node.filters.all())


@dataclass
class Operation:
    label: str
    arguments: int = 0
    value_field: str = None


CommonOperations = {
    "isnull": Operation("is empty"),
    "notnull": Operation("is not empty"),
    "fillna": Operation("fill empty values", 1, "string_value"),
}

StringOperations = {
    "lower": Operation("to lowercase"),
    "upper": Operation("to uppercase"),
    "length": Operation("length"),
    "reverse": Operation("reverse"),
    "strip": Operation("strip"),
    "lstrip": Operation("lstrip"),
    "rstrip": Operation("rstrip"),
    "like": Operation("like", 1, "string_value"),
    "contains": Operation("contains", 1, "string_value"),
    "left": Operation("left", 1, "integer_value"),
    "right": Operation("right", 1, "integer_value"),
    "repeat": Operation("repeat", 1, "integer_value"),
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


def get_edit_query(node):
    parent = node.parents.first()
    query = parent.get_query()
    columns = {
        edit.column: compile_function(query, edit).name(edit.column)
        for edit in node.edit_columns.iterator()
    }
    return query.mutate(**columns)


def get_add_query(node):
    query = node.parents.first().get_query()
    return query.mutate(
        [compile_function(query, add).name(add.label) for add in node.add_columns.all()]
    )


def get_rename_query(node):
    query = node.parents.first().get_query()
    parent = node.parents.first()
    columns = [name for name in parent.schema]

    for rename in node.rename_columns.all():
        idx = columns.index(rename.column)
        columns[idx] = query[rename.column].name(rename.new_name)
    return query[columns]


def get_formula_query(node):
    query = node.parents.first().get_query()
    new_columns = {
        formula.label: to_ibis(query, formula.formula)
        for formula in node.formula_columns.iterator()
    }

    return query.mutate(**new_columns)


def get_distinct_query(node):
    query = node.parents.first().get_query()
    distinct_columns = [column.column for column in node.columns.all()]
    columns = [
        query[column].any_value().name(column)
        for column in query.schema()
        if column not in distinct_columns
    ]
    return query.group_by(distinct_columns).aggregate(columns)


NODE_FROM_CONFIG = {
    "input": get_input_query,
    "output": get_output_query,
    "join": get_join_query,
    "aggregation": get_aggregation_query,
    "select": get_select_query,
    "union": get_union_query,
    "sort": get_sort_query,
    "limit": get_limit_query,
    "filter": bigquery,
    "edit": get_edit_query,
    "add": get_add_query,
    "rename": get_rename_query,
    "formula": get_formula_query,
    "distinct": get_distinct_query,
}
