from lib.bigquery import ibis_client


def get_input_query(node):
    conn = ibis_client()
    return conn.table(node._input_dataset.table_id)


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
        left, right, node._join_left, node._join_right
    )
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

    return to_join(right, left[left_col] == right[right_col]).materialize()


NODE_FROM_CONFIG = {"input": get_input_query, "join": get_join_query}
