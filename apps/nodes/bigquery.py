import inspect
import re
from functools import wraps
from itertools import chain

import ibis
import ibis.expr.operations as ops
from ibis.expr.datatypes import String

from apps.base import clients
from apps.base.core.utils import error_name_to_snake
from apps.columns.bigquery import (
    aggregate_columns,
    compile_formula,
    compile_function,
    convert_column,
    get_aggregate_expr,
    get_groups,
)
from apps.filters.bigquery import get_query_from_filters
from apps.nodes.exceptions import JoinTypeError, NodeResultNone
from apps.tables.bigquery import get_query_from_table
from apps.teams.models import OutOfCreditsException

from ._sentiment_utils import CreditException, get_gcp_sentiment
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

    value = re.sub(re.compile("[\(\) @€$%&^*+-]"), "_", value)
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

    return (
        query.materialize()
        .drop(list(drops))
        .relabel({key: value for key, value in relabels.items() if key not in drops})
    )


def get_aggregation_query(node, query):
    groups = get_groups(query, node)
    return aggregate_columns(query, node, groups)


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

    # the new column names consist of the unique values inside the selected column
    names_query = (
        _format_literal(row[node.pivot_column], column_type)
        for row in client.get_query_results(
            parent[[node.pivot_column]].distinct().compile()
        ).rows_dict
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
            order_by=ops.SortKey(query[window.order_by], window.ascending).to_expr()
            if window.order_by
            else None,
        )
        aggregation = aggregation.over(w)
        aggregations.append(aggregation)
    query = query.mutate(aggregations)
    return query


def get_sentiment_query(node, parent):
    table = getattr(node, "intermediate_table", None)
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
            raise err

        # input node zero state
        if results.get(node) is None:
            raise NodeResultNone(node=node)

    return results[node]
