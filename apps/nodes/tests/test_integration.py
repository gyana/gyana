import json

import pytest

from apps.base.tests.asserts import (
    assertFormRenders,
    assertOK,
    assertSelectorLength,
    assertSelectorText,
)
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


def field_with_default(field, data, default):
    return {field: data.get(field, default)}


def base_formset(formset):
    return {
        f"{formset}-TOTAL_FORMS": 0,
        f"{formset}-MIN_NUM_FORMS": 1000,
        f"{formset}-MAX_NUM_FORMS": 1000,
        f"{formset}-INITIAL_FORMS": 0,
    }


COLUMNS_BASE_DATA = base_formset("columns")
AGGREGATIONS_BASE_DATA = base_formset("aggregations")


def create_and_connect_node(client, kind, node_factory, table, workflow):
    input_node = node_factory(
        kind=Node.Kind.INPUT, input_table=table, workflow=workflow
    )
    node = Node.objects.create(kind=kind, workflow=input_node.workflow, x=50, y=50)
    node.parents.add(input_node)
    node.save()

    r = client.get(f"/nodes/{node.id}")
    assertOK(r)
    return node, r


def update_node(client, id, data):
    r = client.post(f"/nodes/{id}", data={"submit": "Save & Preview", **data})
    assert r.status_code == 303
    return r


def test_input_node(client, setup):
    table, workflow = setup
    r = client.post(
        "/nodes/api/nodes/",
        data={"kind": "input", "workflow": workflow.id, "x": 0, "y": 0},
    )
    assert r.status_code == 201
    input_node = Node.objects.first()
    assert input_node is not None

    r = client.get(f"/nodes/{input_node.id}")
    assertSelectorText(r, "label.checkbox", "olympia")
    assertFormRenders(r, ["input_table", "name", "search"])

    r = update_node(client, input_node.id, {"input_table": table.id})
    input_node.refresh_from_db()

    assert r.status_code == 303
    assert input_node.input_table.id == table.id


def test_input_node_search(with_pg_trgm_extension, client, setup):
    table, workflow = setup
    r = client.post(
        "/nodes/api/nodes/",
        data={"kind": "input", "workflow": workflow.id, "x": 0, "y": 0},
    )
    assert r.status_code == 201
    input_node = Node.objects.first()
    assert input_node is not None

    r = client.post(
        f"/nodes/{id}", data={"submit": "Save & Preview", **{"search": "olympia"}}
    )
    r = client.get(f"/nodes/{input_node.id}")
    assertSelectorText(r, "label.checkbox", "olympia")
    assertSelectorLength(r, "label.checkbox", 1)


def test_output_node(client, node_factory, setup):
    table, workflow = setup
    output_node, r = create_and_connect_node(
        client, Node.Kind.OUTPUT, node_factory, table, workflow
    )

    assertFormRenders(r, ["name"])

    r = update_node(client, output_node.id, {"name": "Outrageous"})
    output_node.refresh_from_db()
    assert output_node.name == "Outrageous"


def test_select_node(client, node_factory, setup):
    table, workflow = setup

    select_node, r = create_and_connect_node(
        client, Node.Kind.SELECT, node_factory, table, workflow
    )
    assertFormRenders(r, ["name", "select_mode", "select_columns"])
    assertSelectorLength(r, "input[name=select_columns]", 8)
    assertSelectorText(r, "label.checkbox[for=id_select_columns_0]", "id")
    assertSelectorText(r, "label.checkbox[for=id_select_columns_4]", "lunch")

    r = update_node(
        client,
        select_node.id,
        {"select_mode": "exclude", "select_columns": ["birthday", "lunch"]},
    )
    select_node.refresh_from_db()
    assert select_node.select_mode == "exclude"
    assert select_node.columns.count() == 2


def test_join_node(client, node_factory, setup):
    table, workflow = setup

    join_node, r = create_and_connect_node(
        client, Node.Kind.JOIN, node_factory, table, workflow
    )
    assertSelectorText(
        r,
        "p",
        "This node needs to be connected to more than one node before you can configure it.",
    )
    second_input = node_factory(
        kind=Node.Kind.INPUT, input_table=table, workflow=workflow
    )
    join_node.parents.add(second_input, through_defaults={"position": 1})

    r = client.get(f"/nodes/{join_node.id}")
    assertOK(r)
    assertFormRenders(r, ["name", "join_how", "join_left", "join_right"])

    r = update_node(
        client,
        join_node.id,
        {"join_how": "outer", "join_left": "id", "join_right": "id"},
    )
    join_node.refresh_from_db()
    assert join_node.join_how == "outer"
    assert join_node.join_left == "id"
    assert join_node.join_right == "id"


def test_aggregation_node(client, node_factory, setup):
    table, workflow = setup

    aggregation_node, r = create_and_connect_node(
        client, Node.Kind.AGGREGATION, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            "name",
            *AGGREGATIONS_BASE_DATA.keys(),
            *COLUMNS_BASE_DATA.keys(),
        ],
    )

    r = update_node(
        client,
        aggregation_node.id,
        {
            **AGGREGATIONS_BASE_DATA,
            **COLUMNS_BASE_DATA,
            "columns-TOTAL_FORMS": 1,
            "columns-0-column": "birthday",
            "columns-0-node": aggregation_node.id,
            "aggregations-0-node": aggregation_node.id,
            "aggregations-TOTAL_FORMS": 1,
            "aggregations-0-column": "id",
            "aggregations-0-function": "sum",
        },
    )
    aggregation_node.refresh_from_db()

    column = aggregation_node.columns.first()
    aggregation = aggregation_node.aggregations.first()
    assert column.column == "birthday"
    assert aggregation.column == "id"
    assert aggregation.function == "sum"


def test_union_node(client, node_factory, setup):
    table, workflow = setup

    union_node, r = create_and_connect_node(
        client, Node.Kind.UNION, node_factory, table, workflow
    )
    assertFormRenders(r, ["name", "union_distinct"])

    r = update_node(client, union_node.id, {"union_distinct": True})
    union_node.refresh_from_db()

    assert union_node.union_distinct == True


def test_except_node(client, node_factory, setup):
    table, workflow = setup

    _, r = create_and_connect_node(
        client, Node.Kind.EXCEPT, node_factory, table, workflow
    )
    assertSelectorText(
        r, ".form__description", "Remove rows that exist in a second table."
    )


def test_intersect_node(client, node_factory, setup):
    table, workflow = setup

    _, _ = create_and_connect_node(
        client, Node.Kind.INTERSECT, node_factory, table, workflow
    )


def test_sort_node(client, node_factory, setup):
    table, workflow = setup

    sort_node, r = create_and_connect_node(
        client, Node.Kind.SORT, node_factory, table, workflow
    )
    sort_base = base_formset("sort_columns")
    assertFormRenders(
        r,
        [
            *sort_base.keys(),
            "name",
            "sort_columns-0-column",
            "sort_columns-0-node",
            "sort_columns-0-id",
            "sort_columns-0-DELETE",
            "sort_columns-0-ascending",
        ],
    )

    r = update_node(
        client,
        sort_node.id,
        {
            **sort_base,
            "sort_columns-TOTAL_FORMS": 1,
            "sort_columns-0-column": "birthday",
            "sort_columns-0-node": sort_node.id,
            "sort_columns-0-ascending": False,
        },
    )
    sort_node.refresh_from_db()

    sort_column = sort_node.sort_columns.first()
    assert sort_column.column == "birthday"
    assert sort_column.ascending == False


def test_limit_node(client, node_factory, setup):
    table, workflow = setup

    limit_node, r = create_and_connect_node(
        client, Node.Kind.LIMIT, node_factory, table, workflow
    )
    assertFormRenders(r, ["name", "limit_limit", "limit_offset"])

    r = update_node(client, limit_node.id, {"limit_limit": 200, "limit_offset": 150})
    limit_node.refresh_from_db()

    assert limit_node.limit_limit == 200
    assert limit_node.limit_offset == 150


def test_filter_node(client, node_factory, setup):
    table, workflow = setup
    filter_base = base_formset("filters")
    filter_node, r = create_and_connect_node(
        client, Node.Kind.FILTER, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            "name",
            *filter_base.keys(),
            "filters-0-node",
            "filters-0-id",
            "filters-0-column",
            "filters-0-DELETE",
        ],
    )

    r = update_node(
        client,
        filter_node.id,
        {
            **filter_base,
            "filters-TOTAL_ROWS": 1,
            "filters-0-node": filter_node.id,
            "filters-0-column": "athlete",
            "filters-0-string_predicate": "isupper",
        },
    )
    filter_node.refresh_from_db()

    filter_column = filter_node.filters.first()
    assert filter_column.column == "athlete"
    assert filter_column.string_predicate == "isupper"


def test_edit_node(client, node_factory, setup):
    table, workflow = setup
    edit_base = base_formset("edit_columns")
    edit_node, r = create_and_connect_node(
        client, Node.Kind.EDIT, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            *edit_base.keys(),
            "name",
            "edit_columns-0-DELETE",
            "edit_columns-0-node",
            "edit_columns-0-id",
            "edit_columns-0-column",
        ],
    )

    r = update_node(
        client,
        edit_node.id,
        {
            **edit_base,
            "edit_columns-0-node": edit_node.id,
            "edit_columns-0-column": "athlete",
            "edit_columns-0-string_function": "isnull",
        },
    )
    edit_node.refresh_from_db()

    edit = edit_node.edit_columns.first()
    assert edit.column == "athlete"
    assert edit.string_function == "isnull"


def test_add_node(client, node_factory, setup):
    table, workflow = setup
    add_base = base_formset("add_columns")
    add_node, r = create_and_connect_node(
        client, Node.Kind.ADD, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            *add_base.keys(),
            "name",
            "add_columns-0-DELETE",
            "add_columns-0-node",
            "add_columns-0-id",
            "add_columns-0-column",
        ],
    )

    r = update_node(
        client,
        add_node.id,
        {
            **add_base,
            "add_columns-0-node": add_node.id,
            "add_columns-0-column": "athlete",
            "add_columns-0-string_function": "isnull",
            "add_columns-0-label": "winner",
        },
    )
    add_node.refresh_from_db()

    add = add_node.add_columns.first()
    assert add.column == "athlete"
    assert add.string_function == "isnull"
    assert add.label == "winner"


def test_rename_node(client, node_factory, setup):
    table, workflow = setup
    rename_base = base_formset("rename_columns")
    rename_node, r = create_and_connect_node(
        client, Node.Kind.RENAME, node_factory, table, workflow
    )

    assertFormRenders(
        r,
        [
            *rename_base.keys(),
            "name",
            "rename_columns-0-node",
            "rename_columns-0-id",
            "rename_columns-0-column",
            "rename_columns-0-new_name",
            "rename_columns-0-DELETE",
        ],
    )

    r = update_node(
        client,
        rename_node.id,
        {
            **rename_base,
            "rename_columns-0-node": rename_node.id,
            "rename_columns-0-column": "birthday",
            "rename_columns-0-new_name": "dob",
        },
    )
    rename_node.refresh_from_db()

    rename = rename_node.rename_columns.first()
    assert rename.column == "birthday"
    assert rename.new_name == "dob"


def test_formula_node(client, node_factory, setup):
    table, workflow = setup
    formula_base = base_formset("formula_columns")
    formula_node, r = create_and_connect_node(
        client, Node.Kind.FORMULA, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            *formula_base.keys(),
            "name",
            "formula_columns-0-formula",
            "formula_columns-0-node",
            "formula_columns-0-id",
            "formula_columns-0-label",
            "formula_columns-0-DELETE",
        ],
    )

    r = update_node(
        client,
        formula_node.id,
        {
            **formula_base,
            "formula_columns-0-formula": "upper(athlete)",
            "formula_columns-0-node": formula_node.id,
            "formula_columns-0-label": "big_athlete",
        },
    )
    formula_node.refresh_from_db()

    formula = formula_node.formula_columns.first()
    assert formula.formula == "upper(athlete)"
    assert formula.label == "big_athlete"


def test_distinct_node(client, node_factory, setup):
    table, workflow = setup

    distinct_node, r = create_and_connect_node(
        client, Node.Kind.DISTINCT, node_factory, table, workflow
    )
    assertFormRenders(r, ["distinct_columns", "name"])

    r = update_node(client, distinct_node.id, {"distinct_columns": ["id", "lunch"]})
    distinct_node.refresh_from_db()

    assert distinct_node.columns.count() == 2


def test_window_node(client, node_factory, setup):
    table, workflow = setup
    window_base = base_formset("window_columns")
    window_node, r = create_and_connect_node(
        client, Node.Kind.WINDOW, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            *window_base.keys(),
            "name",
            "window_columns-0-column",
            "window_columns-0-node",
            "window_columns-0-id",
            "window_columns-0-DELETE",
        ],
    )

    r = update_node(
        client,
        window_node.id,
        {
            **window_base,
            "window_columns-0-column": "id",
            "window_columns-0-function": "sum",
            "window_columns-0-node": window_node.id,
            "window_columns-0-group_by": "birthday",
            "window_columns-0-label": "sum_id",
        },
    )
    window_node.refresh_from_db()

    window = window_node.window_columns.first()
    assert window.column == "id"
    assert window.function == "sum"
    assert window.group_by == "birthday"
    assert window.label == "sum_id"


def test_pivot_node(client, node_factory, setup):
    table, workflow = setup
    pivot_node, r = create_and_connect_node(
        client, Node.Kind.PIVOT, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            "name",
            "pivot_index",
            "pivot_column",
            "pivot_value",
        ],
    )

    r = update_node(
        client,
        pivot_node.id,
        {
            "pivot_index": "id",
            "pivot_column": "birthday",
            "pivot_value": "athlete",
            "pivot_aggregation": "count",
        },
    )
    pivot_node.refresh_from_db()

    assert pivot_node.pivot_index == "id"
    assert pivot_node.pivot_column == "birthday"
    assert pivot_node.pivot_value == "athlete"
    assert pivot_node.pivot_aggregation == "count"


def test_unpivot_node(client, node_factory, setup):
    table, workflow = setup
    secondary_base = base_formset("secondary_columns")
    unpivot_node, r = create_and_connect_node(
        client, Node.Kind.UNPIVOT, node_factory, table, workflow
    )
    assertFormRenders(
        r,
        [
            *COLUMNS_BASE_DATA.keys(),
            "columns-0-id",
            "columns-0-column",
            "columns-0-node",
            "columns-0-DELETE",
            *secondary_base.keys(),
            "name",
            "unpivot_column",
            "unpivot_value",
        ],
    )

    r = update_node(
        client,
        unpivot_node.id,
        {
            **COLUMNS_BASE_DATA,
            **secondary_base,
            "unpivot_column": "category",
            "unpivot_value": "value",
            "columns-TOTAL_ROWS": 1,
            "columns-0-column": "athlete",
            "columns-0-node": unpivot_node.id,
        },
    )
    unpivot_node.refresh_from_db()

    assert unpivot_node.columns.first().column == "athlete"
    assert unpivot_node.unpivot_column == "category"
    assert unpivot_node.unpivot_value == "value"


def test_sentiment_node(client, logged_in_user, node_factory, setup):
    table, workflow = setup

    sentiment_node, r = create_and_connect_node(
        client, Node.Kind.SENTIMENT, node_factory, table, workflow
    )
    assertFormRenders(
        r, ["sentiment_column", "name", "always_use_credits", "credit_confirmed_user"]
    )
    # Should only have the empty and string option
    assertSelectorLength(r, "#id_sentiment_column > option", 2)

    r = update_node(
        client,
        sentiment_node.id,
        {
            "credit_confirmed_user": logged_in_user.id,
            "sentiment_column": "athlete",
            "always_use_credits": True,
        },
    )
    sentiment_node.refresh_from_db()

    assert sentiment_node.sentiment_column == "athlete"
    assert sentiment_node.always_use_credits == True


def test_convert_node(client, node_factory, setup):
    table, workflow = setup
    convert_base = base_formset("convert_columns")
    convert_node, r = create_and_connect_node(
        client, Node.Kind.CONVERT, node_factory, table, workflow
    )

    assertFormRenders(
        r,
        [
            *convert_base.keys(),
            "name",
            "convert_columns-0-node",
            "convert_columns-0-id",
            "convert_columns-0-column",
            "convert_columns-0-target_type",
            "convert_columns-0-DELETE",
        ],
    )

    r = update_node(
        client,
        convert_node.id,
        {
            **convert_base,
            "convert_columns-0-node": convert_node.id,
            "convert_columns-0-column": "id",
            "convert_columns-0-target_type": "text",
        },
    )
    convert_node.refresh_from_db()

    convert = convert_node.convert_columns.first()
    assert convert.column == "id"
    assert convert.target_type == "text"
