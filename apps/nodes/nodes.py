import ibis
from apps.filters.bigquery import create_filter_query
from lib.bigquery import query_table
from lib.clients import bigquery_client, ibis_client
from lib.dag import create_or_replace_intermediate_table, get_parent_updated
from lib.formulas import to_ibis
from lib.operations import compile_function
from lib.pivot import create_pivot_query, create_unpivot_query
from lib.utils import JOINS, get_aggregate_expr, get_join_expr, rename_duplicates


def get_input_query(node):
    return (
        query_table(node.input_table.bq_table, node.input_table.bq_dataset)
        if node.input_table
        else None
    )


def get_output_query(node, parent):
    return parent


def get_select_query(node, parent):
    columns = [col.column for col in node.columns.all()]

    if node.select_mode == "keep":
        return parent.projection(columns or [])

    return parent.drop(columns)


def get_join_query(node, left, right):

    # Adding 1/2 to left/right if the column exists in both tables
    left, right, left_col, right_col = rename_duplicates(
        left, right, node.join_left, node.join_right
    )
    to_join = get_join_expr(left, node.join_how)

    return to_join(right, left[left_col] == right[right_col]).materialize()


def get_aggregation_query(node, query):
    groups = [col.column for col in node.columns.all()]
    aggregations = [
        get_aggregate_expr(query, agg.column, agg.function)
        for agg in node.aggregations.all()
    ]
    if groups:
        query = query.group_by(groups)
    if aggregations:
        return query.aggregate(aggregations)
    return query.size()


def get_union_query(node, query, *queries):
    colnames = query.schema()
    for parent in queries:
        if node.union_mode == "keep":
            query = query.union(parent, distinct=node.union_distinct)
        else:
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
    return create_filter_query(query, node.filters.all())


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
    columns = query.schema().names

    for rename in node.rename_columns.all():
        idx = columns.index(rename.column)
        columns[idx] = query[rename.column].name(rename.new_name)
    return query[columns]


def get_formula_query(node, query):
    new_columns = {
        formula.label: to_ibis(query, formula.formula)
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
    return query.group_by(distinct_columns).aggregate(columns)


def get_pivot_query(node, query):
    table = node.intermediate_table
    conn = ibis_client()

    # If the table doesn't need updating we can simply return the previous computed pivot table
    if table and table.data_updated > max(tuple(get_parent_updated(node))):
        return conn.table(table.bq_table, database=table.bq_dataset)

    client = bigquery_client()
    query = create_pivot_query(node, query, client)
    table = create_or_replace_intermediate_table(table, node, query)

    return conn.table(table.bq_table, database=table.bq_dataset)


def get_unpivot_query(node, query):
    table = node.intermediate_table
    conn = ibis_client()

    # If the table doesn't need updating we can simply return the previous computed pivot table
    if table and table.data_updated > max(tuple(get_parent_updated(node))):
        return conn.table(table.bq_table, database=table.bq_dataset)

    query = create_unpivot_query(node, query)
    table = create_or_replace_intermediate_table(table, node, query)

    return conn.table(table.bq_table, database=table.bq_dataset)


def get_window_query(node, query):
    for window in node.window_columns.all():
        aggregation = get_aggregate_expr(query, window.column, window.function).name(
            window.label
        )

        if window.group_by or window.order_by:
            w = ibis.window(group_by=window.group_by, order_by=window.order_by)
            aggregation = aggregation.over(w)
        query = query.mutate([aggregation])
    return query


NODE_FROM_CONFIG = {
    "input": get_input_query,
    "output": get_output_query,
    "join": get_join_query,
    "aggregation": get_aggregation_query,
    "select": get_select_query,
    "union": get_union_query,
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
}
