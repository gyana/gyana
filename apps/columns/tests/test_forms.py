import pytest
from django.http import QueryDict
from playwright.sync_api import expect

from apps.base.core.aggregations import AggregationFunctions
from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.base.tests.playwright import playwright_form
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
from apps.columns.models import EditColumn

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


def test_aggregation_form(page):
    form = AggregationColumnForm(schema=TABLE.schema())
    playwright_form(page, form)

    expect(page.locator("form input,select,textarea")).to_have_count(1)
    expect(page.locator("select[name=column] option")).to_have_count(COLUMNS_LENGTH)

    page.locator("select[name=column]").select_option("id")
    expect(page.locator("form input,select,textarea")).to_have_count(2)

    check_values = {choice.value for choice in AggregationFunctions}
    expect(page.locator("select[name=function] option")).to_have_count(
        len(check_values)
    )

    option_values = {
        option.get_attribute("value")
        for option in page.locator("select[name=function] option").all()
    }
    assert option_values == check_values


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


def test_operation_column_form(edit_column_factory):
    column = edit_column_factory()
    form = OperationColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    # Adding a column changes the function field
    data = QueryDict(mutable=True)
    data["column"] = "athlete"
    form = OperationColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"column", "string_function"}
    assertFormChoicesLength(form, "string_function", 13)

    data = QueryDict(mutable=True)
    data["column"] = "birthday"
    form = OperationColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"column", "date_function"}
    assertFormChoicesLength(form, "date_function", 6)


def test_add_column_form(add_column_factory):
    column = add_column_factory()
    form = AddColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    # Adding a column changes the function field
    data = QueryDict(mutable=True)
    data["column"] = "stars"
    form = AddColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"column", "integer_function"}
    assertFormChoicesLength(form, "integer_function", 18)

    data = QueryDict(mutable=True)
    data["column"] = "lunch"
    data["time_function"] = "hour"
    form = AddColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "column",
        "time_function",
        "label",
    }
    assertFormChoicesLength(form, "time_function", 7)


def test_formula_form(formula_column_factory):
    column = formula_column_factory()
    form = FormulaColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"formula", "label"}


def test_window_form(window_column_factory):
    column = window_column_factory()
    form = WindowColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"column"}
    assertFormChoicesLength(form, "column", COLUMNS_LENGTH)

    data = QueryDict(mutable=True)
    data["column"] = "medals"
    form = WindowColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "column",
        "function",
        "group_by",
        "order_by",
        "ascending",
        "label",
    }
    assertFormChoicesLength(form, "function", 7)
    assertFormChoicesLength(form, "group_by", COLUMNS_LENGTH)
    assertFormChoicesLength(form, "order_by", COLUMNS_LENGTH)


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


@pytest.mark.parametrize(
    "edit, fields",
    [
        pytest.param(EditColumn(), ["column"], id="Empty edit"),
        pytest.param(
            EditColumn(column="id"), ["column", "integer_function"], id="Integer column"
        ),
        pytest.param(
            EditColumn(column="id", integer_function="sub"),
            ["column", "integer_function", "float_value"],
            id="Integer column with function",
        ),
        pytest.param(
            EditColumn(column="stars", integer_function="sub"),
            ["column", "integer_function", "float_value"],
            id="Float column",
        ),
        pytest.param(
            EditColumn(column="athlete"),
            ["column", "string_function"],
            id="String column",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="like"),
            ["column", "string_function", "string_value"],
            id="String column with function",
        ),
        pytest.param(
            EditColumn(column="when"),
            ["column", "datetime_function"],
            id="Datetime column",
        ),
        pytest.param(
            EditColumn(column="birthday"), ["column", "date_function"], id="Date column"
        ),
        pytest.param(
            EditColumn(column="lunch"), ["column", "time_function"], id="Time column"
        ),
    ],
)
def test_edit_live_fields(edit, fields):
    form = OperationColumnForm(schema=TABLE.schema(), instance=edit)
    assert form.get_live_fields() == fields


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
