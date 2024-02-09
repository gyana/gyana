import pytest
from django.http import QueryDict

from apps.base.core.aggregations import AggregationFunctions
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


def test_column_form_with_formatting(pwf):
    pwf.render(ColumnFormWithFormatting(schema=TABLE.schema()))

    pwf.assert_fields({"column"})
    pwf.assert_select_options_length("column", COLUMNS_LENGTH)

    pwf.page.locator("form .formatting button").click()
    pwf.assert_fields({"column", "name"})

    pwf.select_value("column", "athlete")  # string
    pwf.assert_fields({"column", "name"})

    pwf.select_value("column", "id")  # integer
    pwf.assert_fields(
        {
            "column",
            "name",
            "rounding",
            "currency",
            "is_percentage",
            "conditional_formatting",
            "positive_threshold",
            "negative_threshold",
        }
    )


def test_aggregation_form(pwf):
    pwf.render(AggregationColumnForm(schema=TABLE.schema()))

    pwf.assert_fields({"column"})
    pwf.assert_select_options_length("column", COLUMNS_LENGTH)

    pwf.select_value("column", "id")
    pwf.assert_fields({"column", "function"})

    pwf.assert_select_options(
        "function", {choice.value for choice in AggregationFunctions}
    )


def test_aggregation_form_with_formatting(pwf):
    pwf.render(AggregationFormWithFormatting(schema=TABLE.schema()))

    pwf.assert_fields({"column"})
    pwf.assert_select_options_length("column", COLUMNS_LENGTH)

    pwf.select_value("column", "id")
    pwf.assert_fields({"column", "function"})

    pwf.assert_select_options(
        "function", {choice.value for choice in AggregationFunctions}
    )

    pwf.page.locator("form .formatting button").click()
    pwf.assert_fields(
        {
            "column",
            "function",
            "name",
            "rounding",
            "currency",
            "is_percentage",
            "conditional_formatting",
            "positive_threshold",
            "negative_threshold",
        }
    )


def test_operation_column_form(pwf):
    pwf.render(OperationColumnForm(schema=TABLE.schema()))

    pwf.assert_fields({"column"})
    pwf.assert_select_options_length("column", COLUMNS_LENGTH)

    pwf.select_value("column", "athlete")
    pwf.assert_fields({"column", "string_function"})
    pwf.assert_select_options_length("string_function", 13)

    pwf.select_value("column", "birthday")
    pwf.assert_fields({"column", "date_function"})
    pwf.assert_select_options_length("date_function", 6)


def test_add_column_form(pwf):
    pwf.render(AddColumnForm(schema=TABLE.schema()))

    pwf.assert_fields({"column"})
    pwf.assert_select_options_length("column", COLUMNS_LENGTH)

    pwf.select_value("column", "stars")
    pwf.assert_fields({"column", "integer_function"})
    pwf.assert_select_options_length("integer_function", 18)

    pwf.select_value("column", "lunch")
    pwf.assert_fields({"column", "time_function"})
    pwf.assert_select_options_length("time_function", 7)

    pwf.select_value("time_function", "hour")
    pwf.assert_fields({"column", "time_function", "label"})


def test_formula_form():
    form = FormulaColumnForm(schema=TABLE.schema())

    assert set(form.fields.keys()) == {"formula", "label"}


def test_window_form(pwf):
    pwf.render(WindowColumnForm(schema=TABLE.schema()))

    # Asserting initial state of the form
    pwf.assert_fields({"column"})
    pwf.assert_select_options_length("column", COLUMNS_LENGTH)

    # Selecting a value from the 'column' dropdown and asserting the appearance of new fields
    pwf.select_value("column", "medals")
    pwf.assert_fields(
        {"column", "function", "group_by", "order_by", "ascending", "label"}
    )

    # Asserting the number of options in the 'function', 'group_by', and 'order_by' dropdowns
    pwf.assert_select_options_length("function", 7)
    pwf.assert_select_options_length("group_by", COLUMNS_LENGTH)
    pwf.assert_select_options_length("order_by", COLUMNS_LENGTH)


def test_convert_form(convert_column_factory):
    form = ConvertColumnForm(schema=TABLE.schema())

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
    "select, fields",
    [
        pytest.param({}, ["column"], id="Empty edit"),
        pytest.param(
            {"column": "id"}, ["column", "integer_function"], id="Integer column"
        ),
        pytest.param(
            {"column": "id", "integer_function": "sub"},
            ["column", "integer_function", "float_value"],
            id="Integer column with function",
        ),
        pytest.param(
            {"column": "stars", "integer_function": "sub"},
            ["column", "integer_function", "float_value"],
            id="Float column",
        ),
        pytest.param(
            {"column": "athlete"},
            ["column", "string_function"],
            id="String column",
        ),
        pytest.param(
            {"column": "athlete", "string_function": "like"},
            ["column", "string_function", "string_value"],
            id="String column with function",
        ),
        pytest.param(
            {"column": "when"},
            ["column", "datetime_function"],
            id="Datetime column",
        ),
        pytest.param(
            {"column": "birthday"}, ["column", "date_function"], id="Date column"
        ),
        pytest.param(
            {"column": "lunch"}, ["column", "time_function"], id="Time column"
        ),
    ],
)
def test_edit_live_fields(select, fields, pwf):
    pwf.render(OperationColumnForm(schema=TABLE.schema()))

    for k, v in select.items():
        pwf.select_value(k, v)

    pwf.assert_fields(set(fields))


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
