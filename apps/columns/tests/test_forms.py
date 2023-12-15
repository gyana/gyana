import pytest
from django.http import QueryDict

from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.columns.forms import (
    AddColumnForm,
    AggregationColumnForm,
    AggregationFormWithFormatting,
    ColumnFormWithFormatting,
    ConvertColumnForm,
    FormulaColumnForm,
    JoinColumnForm,
    OperationColumnForm,
    RenameColumnForm,
    WindowColumnForm,
)
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db

COLUMNS_LENGTH = 10


def test_column_form_with_formatting(column_factory, node_factory):
    column = column_factory(node=node_factory())
    form = ColumnFormWithFormatting(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column", "sort_index"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    data = QueryDict(mutable=True)
    data["column"] = "id"
    form = ColumnFormWithFormatting(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "column",
        "sort_index",
        "currency",
        "name",
        "rounding",
        "formatting_unfolded",
        "is_percentage",
        "conditional_formatting",
        "positive_threshold",
        "negative_threshold",
    }

    data["column"] = "athlete"
    form = ColumnFormWithFormatting(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "column",
        "sort_index",
        "name",
        "formatting_unfolded",
    }


def test_aggregation_form(aggregation_column_factory, node_factory, snapshot):
    column = aggregation_column_factory(node=node_factory())
    form = AggregationColumnForm(instance=column, schema=TABLE.schema())

    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    assert {"show": form.show, "effect": form.effect} == snapshot


def test_aggregation_form_with_formatting(aggregation_column_factory, node_factory):
    column = aggregation_column_factory(node=node_factory())
    form = AggregationFormWithFormatting(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column", "sort_index"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    data = QueryDict(mutable=True)
    data["column"] = "id"
    form = AggregationFormWithFormatting(
        instance=column, schema=TABLE.schema(), data=data
    )
    assert set(form.fields.keys()) == {
        "column",
        "sort_index",
        "function",
        "currency",
        "name",
        "rounding",
        "formatting_unfolded",
        "is_percentage",
        "conditional_formatting",
        "positive_threshold",
        "negative_threshold",
    }

    data["column"] = "athlete"
    form = AggregationFormWithFormatting(
        instance=column, schema=TABLE.schema(), data=data
    )
    assert set(form.fields.keys()) == {
        "column",
        "sort_index",
        "function",
        "name",
        "formatting_unfolded",
        "currency",
        "rounding",
        "formatting_unfolded",
        "is_percentage",
        "conditional_formatting",
        "positive_threshold",
        "negative_threshold",
    }


def test_operation_column_form(edit_column_factory, snapshot):
    column = edit_column_factory()
    form = OperationColumnForm(instance=column, schema=TABLE.schema())

    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    assertFormChoicesLength(form, "string_function", 13)
    assertFormChoicesLength(form, "date_function", 6)
    assert {"show": form.show, "effect": form.effect} == snapshot


def test_add_column_form(add_column_factory, snapshot):
    column = add_column_factory()
    form = AddColumnForm(instance=column, schema=TABLE.schema())

    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    assertFormChoicesLength(form, "integer_function", 18)
    assertFormChoicesLength(form, "time_function", 7)
    assert {"show": form.show, "effect": form.effect} == snapshot


def test_formula_form(formula_column_factory):
    column = formula_column_factory()
    form = FormulaColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"formula", "label"}


def test_window_form(window_column_factory, snapshot):
    column = window_column_factory()
    form = WindowColumnForm(instance=column, schema=TABLE.schema())

    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)
    assertFormChoicesLength(form, "group_by", COLUMNS_LENGTH)
    assertFormChoicesLength(form, "order_by", COLUMNS_LENGTH)

    assert {"show": form.show, "effect": form.effect} == snapshot


def test_convert_form(convert_column_factory):
    column = convert_column_factory()
    form = ConvertColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column", "target_type"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)
    assertFormChoicesLength(form, "target_type", 8)


def test_join_form(
    join_column_factory, node_factory, bigquery, integration_table_factory
):
    mock_bq_client_with_schema(
        bigquery, [(name, str(type_)) for name, type_ in TABLE.schema().items()]
    )
    table = integration_table_factory()
    input_node = node_factory(kind=Node.Kind.INPUT, input_table=table)
    second_input = node_factory(kind=Node.Kind.INPUT, input_table=table)
    join_node = node_factory(kind=Node.Kind.JOIN)
    join_node.parents.add(input_node)
    join_node.parents.add(second_input, through_defaults={"position": 1})
    join_node.save()

    column = join_column_factory(node=join_node)
    form = JoinColumnForm(
        instance=column,
        schema=TABLE.schema(),
        parent_instance=column.node,
        prefix="join-column-0",
    )
    assert set(form.fields.keys()) == {
        "left_column",
        "right_column",
        "how",
    }
    assertFormChoicesLength(form, "left_column", 2)
    assertFormChoicesLength(form, "right_column", COLUMNS_LENGTH)
    assertFormChoicesLength(form, "how", 4)


def test_edit_form(edit_column_factory, snapshot):
    column = edit_column_factory()
    form = OperationColumnForm(instance=column, schema=TABLE.schema())

    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    assert {"show": form.show, "effect": form.effect} == snapshot


def test_rename_form(rename_column_factory):
    column = rename_column_factory()
    form = RenameColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column", "new_name"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    # test validation errors
    prefix = "rename_column-0"
    data = QueryDict(mutable=True)
    data[f"{prefix}-column"] = "lunch"
    data[f"{prefix}-new_name"] = "athlete"

    form = RenameColumnForm(
        instance=column, schema=TABLE.schema(), prefix=prefix, data=data
    )
    form.is_valid()
    assert form.errors["new_name"] == ["This column already exists"]

    data[f"{prefix}-new_name"] = "Athlete"
    form = RenameColumnForm(
        instance=column, schema=TABLE.schema(), prefix=prefix, data=data
    )
    form.is_valid()
    assert form.errors["new_name"] == [
        "This column already exists with a different capitalisation"
    ]

    # Test whether it works with virtual columns
    prefix = "rename_column-1"
    first_prefix = "rename_column-0"
    data = QueryDict(mutable=True)
    data[f"{first_prefix}-column"] = "athlete"
    data[f"{first_prefix}-new_name"] = "brunch"
    data[f"{prefix}-column"] = "lunch"
    data[f"{prefix}-new_name"] = "brunch"

    form = RenameColumnForm(
        instance=column, schema=TABLE.schema(), prefix=prefix, data=data
    )
    form.is_valid()
    assert form.errors["new_name"] == ["This column already exists"]
