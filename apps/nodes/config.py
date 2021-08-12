import functools

NODE_CONFIG = {
    "input": {
        "displayName": "Get data",
        "icon": "fa-file",
        "description": "Select a table from an Integration or previous Workflow",
        "section": "Input/Output",
    },
    "output": {
        "displayName": "Save data",
        "icon": "fa-save",
        "description": "Save result as a new table",
        "section": "Input/Output",
    },
    "select": {
        "displayName": "Select columns",
        "icon": "fa-mouse-pointer",
        "description": "Select columns from the table",
        "section": "Table manipulations",
    },
    "join": {
        "displayName": "Join",
        "icon": "fa-link",
        "description": "Combine rows from two tables based on a common column",
        "section": "Table manipulations",
    },
    "aggregation": {
        "displayName": "Aggregation",
        "icon": "fa-object-group",
        "description": "Aggregate values by grouping columns",
        "section": "Table manipulations",
    },
    "union": {
        "displayName": "Union",
        "icon": "fa-plus-square",
        "description": "Combine two or more tables on top of each other",
        "section": "Table manipulations",
    },
    "sort": {
        "displayName": "Sort",
        "icon": "fa-sort-numeric-up",
        "description": "Sort rows by the values of the specified columns",
        "section": "Table manipulations",
    },
    "limit": {
        "displayName": "Limit",
        "icon": "fa-sliders-h-square",
        "description": "Keep a set number of of rows",
        "section": "Table manipulations",
    },
    "filter": {
        "displayName": "Filter",
        "icon": "fa-filter",
        "description": "Filter rows by specified criteria",
        "section": "Table manipulations",
    },
    "edit": {
        "displayName": "Edit",
        "icon": "fa-edit",
        "description": "Change a columns value",
        "section": "Column manipulations",
    },
    "add": {
        "displayName": "Add",
        "icon": "fa-plus",
        "description": "Add new columns to the table",
        "section": "Column manipulations",
    },
    "rename": {
        "displayName": "Rename",
        "icon": "fa-keyboard",
        "description": "Rename columns",
        "section": "Column manipulations",
    },
    "text": {
        "displayName": "Text",
        "icon": "fa-text",
        "description": "Annotate your workflow",
        "section": "Annotation",
    },
    "formula": {
        "displayName": "Formula",
        "icon": "fa-function",
        "description": "Add a new column using a formula",
        "section": "Column manipulations",
    },
    "distinct": {
        "displayName": "Distinct",
        "icon": "fa-fingerprint",
        "description": "Select unqiue values from selected columns",
        "section": "Table manipulations",
    },
    "pivot": {
        "displayName": "Pivot",
        "icon": "fa-redo-alt",
        "description": "Pivot your table",
        "section": "Table manipulations",
    },
    "unpivot": {
        "displayName": "Unpivot",
        "icon": "fa-undo-alt",
        "description": "Unpivot your table",
        "section": "Table manipulations",
    },
    "intersect": {
        "displayName": "Intersection",
        "icon": "fa-intersection",
        "description": "Find the common rows between tables",
        "section": "Table manipulations",
    },
    "window": {
        "displayName": "Window",
        "icon": "fa-window-frame",
        "description": "Calculate analytics over groups without aggregating",
        "section": "Column manipulations",
    },
}


def _add_max_parents(name):
    from apps.nodes.bigquery import NODE_FROM_CONFIG, get_arity_from_node_func

    func = NODE_FROM_CONFIG.get(name, None)
    # 0, False for text node
    min_arity, variable_args = get_arity_from_node_func(func) if func else (0, False)
    return -1 if variable_args else min_arity


@functools.cache
def get_node_config_with_arity():
    return {k: {**v, "maxParents": _add_max_parents(k)} for k, v in NODE_CONFIG.items()}
