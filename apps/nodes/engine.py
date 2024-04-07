import inspect
import re
from functools import wraps
from itertools import chain

import ibis
import ibis.expr.datatypes as dt
import ibis.expr.operations as ops
from cacheops import cached_as
from ibis.expr.datatypes import String

from apps.base import engine
from apps.base.clients import get_engine
from apps.base.core.utils import error_name_to_snake
from apps.base.engine import bigquery as bq
from apps.columns.engine import (
    aggregate_columns,
    compile_formula,
    compile_function,
    convert_column,
    get_aggregate_expr,
    get_groups,
)
from apps.filters.engine import get_query_from_filters
from apps.nodes.exceptions import ColumnNamesDontMatch, JoinTypeError, NodeResultNone
from apps.nodes.models import Node

from ._utils import create_or_replace_intermediate_table, get_parent_updated


def _rename_duplicates(queries):
    column_names = list(chain(*[q.schema() for q in queries]))
    duplicates = {
        name
        for name in column_names
        if [c.lower() for c in column_names].count(name.lower()) > 1
    }

    duplicate_map = {}
    renamed_queries = []
    for idx, query in enumerate(queries):
        relabels = {
            column: f"{column}_{idx+1}"
            for column in query.schema()
            if column in duplicates
        }

        renamed_queries.append(query.relabel(relabels))
        duplicate_map[idx] = relabels

    return renamed_queries, duplicate_map


def _format_string(value):
    if not re.compile("^[a-zA-Z_].*").match(value):
        value = f"_{value}"

    value = re.sub(re.compile("[\(\) \\\/@€$%&^*+-]"), "_", value)
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
        table = getattr(node, "intermediate_table", None)
        conn = engine.get_engine().client

        # if the table doesn't need updating we can simply return the previous computed pivot table
        if table and table.data_updated > max(tuple(get_parent_updated(node))):
            return conn.table(table.name, database=table.namespace)

        query = func(node, parent)
        table = create_or_replace_intermediate_table(node, query)

        return conn.table(table.name, database=table.namespace)

    return wrapper


def get_input_query(node):
    return get_engine().get_table(node.input_table) if node.input_table else None


def get_output_query(node, parent):
    return parent


def get_select_query(node, parent):
    columns = [col.column for col in node.columns.all()]

    if node.select_mode == "keep":
        columns = columns or parent.columns
        return parent.projection([parent[column] for column in columns])

    return parent.drop(columns)


def get_join_query(node, left, right, *queries):
    renamed_queries, duplicate_map = _rename_duplicates([left, right, *queries])

    query = renamed_queries[0]
    drops = set()
    relabels = {}
    for idx, join in enumerate(node.join_columns.all()[: len(renamed_queries) - 1]):
        left = renamed_queries[join.left_index]
        right = renamed_queries[idx + 1]

        left_col = duplicate_map[join.left_index].get(
            join.left_column, join.left_column
        )
        right_col = duplicate_map[idx + 1].get(join.right_column, join.right_column)
        try:
            query = query.join(right, left[left_col] == right[right_col], how=join.how)
        except TypeError:
            # We don't to display the original column names (instead of the potentiall
            # suffixed left_col or right_col)
            # but need to fetch the type from the right table
            raise JoinTypeError(
                left_column_name=join.left_column,
                right_column_name=join.right_column,
                left_column_type=left[left_col].type(),
                right_column_type=right[right_col].type(),
            )

        if join.how == "inner":
            drops.add(right_col)
            relabels[left_col] = join.left_column

    return query.drop(list(drops)).relabel(
        {key: value for key, value in relabels.items() if key not in drops}
    )


def get_aggregation_query(node, query):
    groups = get_groups(query, node)
    return aggregate_columns(query, node.aggregations.all(), groups)


def get_union_query(node, query, *queries):
    columns = query.schema()
    for idx, parent in enumerate(queries):
        if set(parent.schema()) != set(columns):
            raise ColumnNamesDontMatch(
                index=idx,
                left_columns=set(columns) - set(parent.schema()),
                right_columns=set(parent.schema()) - set(columns),
            )

        # Project to make sure columns are in the same order
        parent = parent.projection([parent[column] for column in columns])
        if parent.schema().types != query.schema().types:
            # We can cast integer columns to float columns to make the union possible
            # we need to do it for query or parent depending which source contains the
            # integer column
            p_castings = {}
            q_castings = {}
            for colname in columns:
                if isinstance(parent[colname].type(), dt.Integer) and isinstance(
                    query[colname].type(), (dt.Floating, dt.Decimal)
                ):
                    p_castings[colname] = parent[colname].cast(query[colname].type())
                elif isinstance(query[colname].type(), dt.Integer) and isinstance(
                    parent[colname].type(), (dt.Floating, dt.Decimal)
                ):
                    q_castings[colname] = query[colname].cast(parent[colname].type())
            query = query.mutate(**q_castings)
            parent = parent.mutate(**p_castings)

        query = query.union(parent, distinct=node.union_distinct)
    # Need to `select *` so we can operate on the query
    return query[query]


def get_except_query(node, query, *queries):
    for parent in queries:
        query = query.difference(parent)
    # Need to `select *` so we can operate on the query
    return query[query]


def get_intersect_query(node, query, *queries):
    for parent in queries:
        query = query.intersect(parent)

    # Need to `select *` so we can operate on the query
    return query[query]


def get_sort_query(node, query):
    sort_columns = [
        getattr(query, s.column) if s.ascending else ibis.desc(getattr(query, s.column))
        for s in node.sort_columns.all()
    ]
    return query.order_by(sort_columns)


def get_limit_query(node, query):
    # Need to project again to make sure limit isn't overwritten
    query = query.limit(node.limit_limit, offset=node.limit_offset or 0)
    return query[query]


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
    column_type = parent[node.pivot_column].type()

    # the new column names consist of the unique values inside the selected column
    names_query = (
        _format_literal(row[node.pivot_column], column_type)
        for _, row in parent[[node.pivot_column]].distinct().execute().iterrows()
    )
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

        w = ibis.window(
            group_by=window.group_by or None,
            order_by=(
                ops.SortKey(query[window.order_by], window.ascending).to_expr()
                if window.order_by
                else None
            ),
        )
        aggregation = aggregation.over(w)
        aggregations.append(aggregation)
    query = query.mutate(aggregations)
    return query


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


@cached_as(Node, timeout=60)
def get_query_from_node(current_node):
    nodes = _get_all_parents(current_node)
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
                node.save()
        except Exception as err:
            node.error = error_name_to_snake(err)
            node.save()
            if current_node != node:
                raise NodeResultNone(node=node) from err
            raise err

        # input node zero state
        if results.get(node) is None:
            raise NodeResultNone(node=node)

    return results[node]
