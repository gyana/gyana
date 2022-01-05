import inspect
import logging
import re
from functools import wraps

import ibis
from ibis.expr.datatypes import String

from apps.base import clients
from apps.base.errors import error_name_to_snake
from apps.columns.bigquery import (
    aggregate_columns,
    compile_formula,
    compile_function,
    convert_column,
    get_aggregate_expr,
)
from apps.filters.bigquery import get_query_from_filters
from apps.tables.bigquery import get_query_from_table
from apps.teams.models import OutOfCreditsException

from ._sentiment_utils import CreditException, get_gcp_sentiment
from ._utils import create_or_replace_intermediate_table, get_parent_updated

JOINS = {
    "inner": "inner_join",
    "outer": "outer_join",
    "left": "left_join",
    "right": "right_join",
}


def _get_duplicate_names(left, right):
    left_names = {col.lower() for col in left.schema()}
    right_names = {col.lower() for col in right.schema()}
    return left_names & right_names


def _rename_duplicates(left, right, left_col, right_col):
    duplicates = _get_duplicate_names(left, right)
    left = left.relabel(
        {col: f"{col}_left" for col in left.columns if col.lower() in duplicates}
    )
    right = right.relabel(
        {col: f"{col}_right" for col in right.columns if col.lower() in duplicates}
    )
    left_col = f"{left_col}_left" if left_col in duplicates else left_col
    right_col = f"{right_col}_right" if right_col in duplicates else right_col

    return left, right, left_col, right_col


def _format_string(value):
    if not re.compile("[a-zA-Z_]").match(value[0]):
        value = "_" + value[1:]

    value = re.sub(re.compile("[\(\) @$%€^&*-+]"), "_", value)
    return value


def _format_literal(value, type_):
    """Formats a value to the right SQL type to be used in a string query.

    Wraps a string in quotes and replaces spaces from values with `_`
    """
    if value is None:
        return "null"
    if isinstance(type_, String):
        return f'"{value}" {_format_string(value)}'
    return str(value)


def use_intermediate_table(func):
    @wraps(func)
    def wrapper(node, parent):

        table = node.intermediate_table
        conn = clients.ibis_client()

        # if the table doesn't need updating we can simply return the previous computed pivot table
        if table and table.data_updated > max(tuple(get_parent_updated(node))):
            return conn.table(table.bq_table, database=table.bq_dataset)

        query = func(node, parent)
        table = create_or_replace_intermediate_table(node, query)

        return conn.table(table.bq_table, database=table.bq_dataset)

    return wrapper


def get_input_query(node):
    return get_query_from_table(node.input_table) if node.input_table else None


def get_output_query(node, parent):
    return parent


def get_select_query(node, parent):
    columns = [col.column for col in node.columns.all()]

    if node.select_mode == "keep":
        return parent.projection(columns or [])

    return parent.drop(columns)


def get_join_query(node, left, right):

    # Adding left/right to left/right if the column exists in both tables
    left, right, left_col, right_col = _rename_duplicates(
        left, right, node.join_left, node.join_right
    )
    to_join = getattr(left, JOINS[node.join_how])

    joined = to_join(right, left[left_col] == right[right_col]).materialize()
    if node.join_how == "inner":
        joined = joined.drop([right_col]).relabel({left_col: node.join_left})
    return joined


def get_aggregation_query(node, query):
    return aggregate_columns(query, node)


def get_union_query(node, query, *queries):
    colnames = query.schema()
    for parent in queries:
        if set(parent.schema()) == set(colnames):
            # Project to make sure columns are in the same order
            query = query.union(
                parent.projection(list(colnames)), distinct=node.union_distinct
            )
        else:
            raise ibis.common.exceptions.RelationError
    # Need to `select *` so we can operate on the query
    return query.projection(colnames)


def get_except_query(node, query, *queries):
    colnames = query.schema()
    for parent in queries:
        query = query.difference(parent)
    # Need to `select *` so we can operate on the query
    return query.projection(colnames)


def get_intersect_query(node, query, *queries):
    colnames = query.schema()
    for parent in queries:
        query = query.intersect(parent)

    # Need to `select *` so we can operate on the query
    return query.projection(colnames)


def get_sort_query(node, query):
    sort_columns = [
        (getattr(query, s.column), s.ascending) for s in node.sort_columns.all()
    ]
    return query.sort_by(sort_columns)


def get_limit_query(node, query):
    # Need to project again to make sure limit isn't overwritten
    return query.limit(node.limit_limit, offset=node.limit_offset or 0).projection(
        query.schema()
    )


def get_filter_query(node, query):
    return get_query_from_filters(query, node.filters.all())


def get_edit_query(node, query):
    columns = {
        edit.column: compile_function(query, edit).name(edit.column)
        for edit in node.edit_columns.iterator()
    }
    return query.mutate(**columns)


def get_add_query(node, query):
    return query.mutate(
        [compile_function(query, add).name(add.label) for add in node.add_columns.all()]
    )


def get_rename_query(node, query):
    return query.relabel(
        {rename.column: rename.new_name for rename in node.rename_columns.all()}
    )


def get_formula_query(node, query):
    new_columns = {
        formula.label: compile_formula(query, formula.formula)
        for formula in node.formula_columns.iterator()
    }

    return query.mutate(**new_columns)


def get_distinct_query(node, query):
    distinct_columns = [column.column for column in node.columns.all()]
    columns = [
        query[column].any_value().name(column)
        for column in query.schema()
        if column not in distinct_columns
    ]
    return (
        query.group_by(distinct_columns).aggregate(columns)
        if distinct_columns
        else query
    )


@use_intermediate_table
def get_pivot_query(node, parent):
    client = clients.bigquery()
    column_type = parent[node.pivot_column].type()

    # the new column names consist of the values inside the selected column
    # and we only need unique values but can't use a set because we like to keep the values
    names_query = {
        _format_literal(row[node.pivot_column], column_type): None
        for row in client.get_query_results(
            parent[node.pivot_column].compile()
        ).rows_dict
    }.keys()
    # `pivot_index` is optional and won't be displayed if not selected
    selection = ", ".join(
        filter(None, (node.pivot_index, node.pivot_column, node.pivot_value))
    )

    return (
        f"SELECT * FROM"
        f"  (SELECT {selection} FROM ({parent.compile()}))"
        f"  PIVOT({node.pivot_aggregation}({node.pivot_value})"
        f"      FOR {node.pivot_column} IN ({', '.join(names_query)})"
        f"  )"
    )


@use_intermediate_table
def get_unpivot_query(node, parent):
    selection_columns = [col.column for col in node.secondary_columns.all()]
    selection = (
        f"{', '.join(selection_columns)+', ' if selection_columns else ''}"
        f"{node.unpivot_column}, "
        f"{node.unpivot_value}"
    )
    return (
        f"SELECT {selection} FROM ({parent.compile()})"
        f" UNPIVOT({node.unpivot_value} FOR {node.unpivot_column} IN ({', '.join([col.column for col in node.columns.all()])}))"
    )


def get_window_query(node, query):
    aggregations = []
    for window in node.window_columns.all():
        aggregation = get_aggregate_expr(
            query, window.column, window.function, []
        ).name(window.label)

        if window.group_by or window.order_by:
            w = ibis.window(group_by=window.group_by, order_by=window.order_by)
            aggregation = aggregation.over(w)
        aggregations.append(aggregation)
    query = query.mutate(aggregations)
    return query


def get_sentiment_query(node, parent):
    table = node.intermediate_table
    conn = clients.ibis_client()

    # if the table doesn't need updating we can simply return the previous computed table
    if table and table.data_updated > max(tuple(get_parent_updated(node))):
        return conn.table(table.bq_table, database=table.bq_dataset)

    task = get_gcp_sentiment.delay(node.id)
    bq_table, bq_dataset = task.wait(timeout=None, interval=0.1)

    return conn.table(bq_table, database=bq_dataset)


def get_convert_query(node, query):
    converted_columns = {
        column.column: convert_column(query, column)
        for column in node.convert_columns.iterator()
    }

    return query.mutate(**converted_columns)


NODE_FROM_CONFIG = {
    "input": get_input_query,
    "output": get_output_query,
    "join": get_join_query,
    "aggregation": get_aggregation_query,
    "select": get_select_query,
    "union": get_union_query,
    "except": get_except_query,
    "sort": get_sort_query,
    "limit": get_limit_query,
    "filter": get_filter_query,
    "edit": get_edit_query,
    "add": get_add_query,
    "rename": get_rename_query,
    "formula": get_formula_query,
    "distinct": get_distinct_query,
    "pivot": get_pivot_query,
    "unpivot": get_unpivot_query,
    "intersect": get_intersect_query,
    "sentiment": get_sentiment_query,
    "window": get_window_query,
    "convert": get_convert_query,
}


def _get_all_parents(node):
    # yield parents before child => topological order
    for parent in node.parents_ordered.all():
        yield from _get_all_parents(parent)
    yield node


def get_arity_from_node_func(func):

    node_arg, *params = inspect.signature(func).parameters.values()

    # testing for "*args" in signature
    variable_args = any(
        param.kind == inspect.Parameter.VAR_POSITIONAL for param in params
    )
    min_arity = len(params) - 1 if variable_args else len(params)

    return min_arity, variable_args


def _validate_arity(func, len_args):

    min_arity, variable_args = get_arity_from_node_func(func)
    return len_args >= min_arity if variable_args else len_args == min_arity


def get_query_from_node(node):

    nodes = _get_all_parents(node)
    # remove duplicates (python dicts are insertion ordered)
    nodes = list(dict.fromkeys(nodes))

    results = {}

    for node in nodes:
        func = NODE_FROM_CONFIG[node.kind]
        args = [results[parent] for parent in node.parents_ordered.all()]

        if not _validate_arity(func, len(args)):
            raise NodeResultNone(node)

        try:
            results[node] = func(node, *args)
            if node.error:
                node.error = None
                # Only update error field to avoid overwriting changes performed
                # In celery (e.g. adding the intermediate table for sentiment)
                node.save(update_fields=["error"])
        except Exception as err:
            node.error = error_name_to_snake(err)
            if isinstance(err, (CreditException, OutOfCreditsException)):
                node.uses_credits = err.uses_credits
            node.save()
            logging.error(err, exc_info=err)

        # input node zero state
        if results.get(node) is None:
            raise NodeResultNone(node=node)

    return results[node]


class NodeResultNone(Exception):
    def __init__(self, node, *args: object) -> None:
        super().__init__(*args)

        self.node = node
