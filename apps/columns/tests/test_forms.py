import pytest
from apps.base.aggregations import AggregationFunctions
from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.columns.forms import (
    AddColumnForm,
    AggregationColumnForm,
    FormulaColumnForm,
    OperationColumnForm,
    WindowColumnForm,
)
from django.http import QueryDict

pytestmark = pytest.mark.django_db


def test_aggregation_form(aggregation_column_factory, node_factory):
    column = aggregation_column_factory(node=node_factory())
    form = AggregationColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"hidden_live", "column"}
    assertFormChoicesLength(form, "column", 9)

    data = QueryDict(mutable=True)
    data["column"] = "id"
    form = AggregationColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"hidden_live", "column", "function"}
    assert {choice[0] for choice in form.fields["function"].choices} == {
        choice.value for choice in AggregationFunctions
    }


def test_operation_column_form(edit_column_factory, node_factory):
    column = edit_column_factory(node=node_factory())
    form = OperationColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"hidden_live", "column"}
    assertFormChoicesLength(form, "column", 9)

    # Adding a column changes the function field
    data = QueryDict(mutable=True)
    data["column"] = "athlete"
    form = OperationColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"hidden_live", "column", "string_function"}
    assertFormChoicesLength(form, "string_function", 13)

    data = QueryDict(mutable=True)
    data["column"] = "birthday"
    form = OperationColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"hidden_live", "column", "date_function"}
    assertFormChoicesLength(form, "date_function", 6)


def test_add_column_form(add_column_factory, node_factory):
    column = add_column_factory(node=node_factory())
    form = AddColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"hidden_live", "column"}
    assertFormChoicesLength(form, "column", 9)

    # Adding a column changes the function field
    data = QueryDict(mutable=True)
    data["column"] = "stars"
    form = AddColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"hidden_live", "column", "integer_function"}
    assertFormChoicesLength(form, "integer_function", 18)

    data = QueryDict(mutable=True)
    data["column"] = "lunch"
    data["time_function"] = "hour"
    form = AddColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "hidden_live",
        "column",
        "time_function",
        "label",
    }
    assertFormChoicesLength(form, "time_function", 7)


def test_formula_form(formula_column_factory, node_factory):
    column = formula_column_factory(node=node_factory())
    form = FormulaColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"hidden_live", "formula", "label"}


def test_window_form(window_column_factory, node_factory):
    column = window_column_factory(node=node_factory())
    form = WindowColumnForm(instance=column, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"hidden_live", "column"}
    assertFormChoicesLength(form, "column", 9)

    data = QueryDict(mutable=True)
    data["column"] = "medals"
    form = WindowColumnForm(instance=column, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "hidden_live",
        "column",
        "function",
        "group_by",
        "order_by",
        "ascending",
        "label",
    }
    assertFormChoicesLength(form, "function", 7)
    assertFormChoicesLength(form, "group_by", 9)
    assertFormChoicesLength(form, "order_by", 9)
