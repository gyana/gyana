def get_duplicate_names(left, right):
    left_names = set(left.schema())
    right_names = set(right.schema())
    return left_names & right_names


def rename_duplicates(left, right, left_col, right_col):
    duplicates = get_duplicate_names(left, right)
    left = left.relabel({d: f"{d}_1" for d in duplicates})
    right = right.relabel({d: f"{d}_2" for d in duplicates})
    left_col = f"{left_col}_1" if left_col in duplicates else left_col
    right_col = f"{right_col}_2" if right_col in duplicates else right_col

    return left, right, left_col, right_col


JOINS = {
    "inner": "inner_join",
    "outer": "outer_join",
    "left": "left_join",
    "right": "right_join",
}


def get_aggregate_expr(query, colname, computation):
    column = getattr(query, colname)
    return getattr(column, computation)().name(colname)
