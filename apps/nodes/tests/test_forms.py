import pytest
from django.http import QueryDict

from apps.nodes.forms import KIND_TO_FORM
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


def create_and_connect(kind, node_factory, table, workflow):
    input_node = node_factory(
        kind=Node.Kind.INPUT, input_table=table, workflow=workflow
    )
    node = node_factory(kind=kind, workflow=workflow, x=50, y=50)
    node.parents.add(input_node)
    return node


def get_choice_len(form, field_name):
    return len(list(form.fields[field_name].choices))


def test_input_form(setup, node_factory):
    table, workflow = setup
    node = node_factory(kind=Node.Kind.INPUT, workflow=workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.get_live_fields()) == {"input_table", "search"}
    table_choices = list(form.fields["input_table"].choices)
    assert len(table_choices) == 2
    assert table_choices[0][0] == ""
    assert table_choices[1][0].instance == table


def test_output_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.OUTPUT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {"name"}
    assert form.fields["name"].label == "Output name"


def test_select_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.SELECT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {"select_mode", "select_columns"}
    assert get_choice_len(form, "select_columns") == 8

    # Test custom save
    data = QueryDict(mutable=True)
    data["select_mode"] = "exclude"
    data["submit"] = "Submit & Preview"
    data.setlist("select_columns", ["birthday", "athlete"])
    form = KIND_TO_FORM[node.kind](instance=node, data=data)
    assert form.is_valid()
    form.save()

    assert node.select_mode == "exclude"
    assert node.columns.count() == 2

    # test custom initial
    form = KIND_TO_FORM[node.kind](instance=node)
    assert len(form.fields["select_columns"].initial) == 2


def test_distinct_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.DISTINCT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {"distinct_columns"}
    assert get_choice_len(form, "distinct_columns") == 8

    # Test custom save
    data = QueryDict(mutable=True)
    data["submit"] = "Submit & Preview"
    data.setlist("distinct_columns", ["birthday", "athlete", "lunch"])
    form = KIND_TO_FORM[node.kind](instance=node, data=data)
    assert form.is_valid()
    form.save()

    assert node.columns.count() == 3

    # test custom initial
    form = KIND_TO_FORM[node.kind](instance=node)
    assert len(form.fields["distinct_columns"].initial) == 3


def test_union_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.UNION, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {"union_distinct"}


def test_limit_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.LIMIT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {"limit_limit", "limit_offset"}


def test_pivot_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.PIVOT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {
        "pivot_value",
        "pivot_index",
        "pivot_column",
    }
    assert get_choice_len(form, "pivot_column") == 9

    # Test that pivot_aggregation is added to fields
    data = QueryDict(mutable=True)
    data["pivot_value"] = "id"
    form = KIND_TO_FORM[node.kind](instance=node, data=data)
    assert set(form.fields.keys()) == {
        "pivot_value",
        "pivot_index",
        "pivot_column",
        "pivot_aggregation",
    }
    assert get_choice_len(form, "pivot_aggregation") == 7


def test_unpivot_form(setup, node_factory):
    table, workflow = setup
    node = create_and_connect(Node.Kind.UNPIVOT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)

    assert set(form.fields.keys()) == {"unpivot_column", "unpivot_value"}


def test_sentiment_form(setup, node_factory, logged_in_user):
    table, workflow = setup
    node = create_and_connect(Node.Kind.SENTIMENT, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node, user=logged_in_user)

    assert set(form.fields.keys()) == {
        "sentiment_column",
        "always_use_credits",
        "credit_confirmed_user",
    }
    assert get_choice_len(form, "sentiment_column") == 2
    assert (
        form.get_initial_for_field(
            form.fields["credit_confirmed_user"], "credit_confirmed_user"
        )
        == logged_in_user
    )


# Test all nodes that only have a default node
def kind_param(kind):
    return pytest.param(kind, id=f"test {kind} form")


@pytest.mark.parametrize(
    "kind",
    [
        kind_param(Node.Kind.AGGREGATION),
        kind_param(Node.Kind.SORT),
        kind_param(Node.Kind.FILTER),
        kind_param(Node.Kind.EDIT),
        kind_param(Node.Kind.ADD),
        kind_param(Node.Kind.RENAME),
        kind_param(Node.Kind.FORMULA),
        kind_param(Node.Kind.INTERSECT),
        kind_param(Node.Kind.WINDOW),
        kind_param(Node.Kind.EXCEPT),
        kind_param(Node.Kind.CONVERT),
        kind_param(Node.Kind.JOIN),
    ],
)
def test_default_form(kind, setup, node_factory):
    table, workflow = setup
    node = create_and_connect(kind, node_factory, table, workflow)
    form = KIND_TO_FORM[node.kind](instance=node)
    assert set(form.fields.keys()) == {}
