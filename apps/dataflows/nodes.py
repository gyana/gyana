from lib.bigquery import ibis_client


def get_input_query(node):
    conn = ibis_client()
    return conn.table(node._input_dataset.table_id)


def get_join_query(node):
    left = node.parents.first().get_query()
    right = node.parents.last().get_query()
    how = node._join_how
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

    return to_join(right, left[node._join_left] == right[node._join_right])[left, right]


NODE_FROM_CONFIG = {"input": get_input_query, "join": get_join_query}
