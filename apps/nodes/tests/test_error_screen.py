from unittest import mock

import pytest

from apps.base.tests.asserts import (
    assertFormRenders,
    assertOK,
    assertSelectorLength,
    assertSelectorText,
)
from apps.nodes.models import Node
from apps.nodes.tests.mocks import mock_bq_client_data, mock_gcp_analyze_sentiment
from apps.teams.models import CreditTransaction

pytestmark = pytest.mark.django_db


def create_node(table, workflow, kind, node_factory, **kwargs):
    input_node = node_factory(
        kind=Node.Kind.INPUT,
        input_table=table,
        workflow=workflow,
    )
    node = node_factory(kind=kind, workflow=workflow, has_been_saved=True, **kwargs)
    node.parents.add(input_node)
    return node


@pytest.mark.parametrize(
    "formula, message",
    [
        pytest.param(
            "does_not_exist(athlete)",
            "Function does_not_exist does not exist.",
            id="function does not exist",
        ),
        pytest.param(
            "join('_', athlete, does_not_exist)",
            "Column does_not_exist does not exist on input",
            id="column does not exist",
        ),
        pytest.param(
            "abs(medals, medals)",
            "Function abs expected at least",
            id="argument error",
        ),
        pytest.param(
            "abs(athlete)",
            "You cannot use abs on column athlete",
            id="column attribute error",
        ),
        pytest.param(
            "001_athlete",
            "We cannot parse the formula",
            id="parsing error",
        ),
    ],
)
def test_formula_error(formula, message, client, setup, node_factory):
    table, workflow = setup

    formula_node = create_node(
        table,
        workflow,
        Node.Kind.FORMULA,
        node_factory,
    )

    formula_node.formula_columns.create(formula=formula, label="doesntmatter")

    r = client.get(f"/nodes/{formula_node.id}/grid")
    assertOK(r)
    assertSelectorText(r, "h2", "Formula error")
    assertSelectorText(r, "p", message)


def test_out_of_credits(mocker, client, setup, node_factory, logged_in_user, bigquery):
    table, workflow = setup
    mock_bq_client_data(bigquery)
    mocker.patch(
        target="apps.nodes._sentiment_utils._gcp_analyze_sentiment",
        side_effect=mock_gcp_analyze_sentiment,
    )
    mocker.patch(
        "apps.nodes._sentiment_utils.LanguageServiceClient",
        side_effect=mock.MagicMock,
    )

    sentiment_node = create_node(
        table,
        workflow,
        Node.Kind.SENTIMENT,
        node_factory,
        sentiment_column="athlete",
        always_use_credits=True,
    )
    team = logged_in_user.teams.first()

    # Add credits so that operation would consume too many credits
    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.INCREASE,
        amount=99,
        user=logged_in_user,
    )

    r = client.get(f"/nodes/{sentiment_node.id}/grid")
    assertOK(r)
    assertSelectorText(r, "body", "99")
    assertSelectorText(r, "h2", "You are about to exceed your credit limit")


def test_credit_exception(client, setup, node_factory):
    table, workflow = setup

    sentiment_node = create_node(
        table,
        workflow,
        Node.Kind.SENTIMENT,
        node_factory,
        sentiment_column="athlete",
    )
    r = client.get(f"/nodes/{sentiment_node.id}/grid")
    assertOK(r)
    assertSelectorLength(r, "#credit-exception", 1)
    assertFormRenders(r, ["always_use_credits"])


def test_integrity_error(client, setup, node_factory):
    table, workflow = setup
    rename_node = create_node(table, workflow, Node.Kind.RENAME, node_factory)

    rename_node.rename_columns.create(column="birthday", new_name="athlete")

    r = client.get(f"/nodes/{rename_node.id}/grid")
    assertOK(r)
    assertSelectorText(
        r,
        "p",
        "The resulting table would have duplicate column names, make sure all column names are unique.",
    )


def test_join_type_error(client, setup, node_factory):
    table, workflow = setup
    join_node = create_node(table, workflow, Node.Kind.JOIN, node_factory)

    second_input_node = node_factory(
        kind=Node.Kind.INPUT,
        input_table=table,
        workflow=workflow,
    )

    join_node.parents.add(second_input_node, through_defaults={"position": 1})

    join_node.join_columns.create(left_column="athlete", right_column="birthday")

    r = client.get(f"/nodes/{join_node.id}/grid")
    assertOK(r)
    assertSelectorText(r, "p", "Cannot join column athlete with birthday")


def test_columns_dont_match_error(client, setup, node_factory):
    table, workflow = setup
    select_node = create_node(table, workflow, Node.Kind.SELECT, node_factory)
    select_node.columns.create(column="athlete")
    union_node = create_node(table, workflow, Node.Kind.UNION, node_factory)

    union_node.parents.add(select_node, through_defaults={"position": 1})
    r = client.get(f"/nodes/{union_node.id}/grid")
    assertOK(r)
    assertSelectorText(
        r,
        ".node__visual",
        "exist in Input 1 but not in Input 2",
    )


def test_relation_error(client, setup, node_factory):
    table, workflow = setup
    convert_node = create_node(table, workflow, Node.Kind.CONVERT, node_factory)
    convert_node.convert_columns.create(column="medals", target_type="date")
    union_node = create_node(table, workflow, Node.Kind.UNION, node_factory)

    union_node.parents.add(convert_node, through_defaults={"position": 1})
    r = client.get(f"/nodes/{union_node.id}/grid")
    assertOK(r)
    assertSelectorText(
        r,
        "p",
        "The incoming tables need to have the same column types in order to merge successfully.",
    )


def raise_error():
    raise Exception


def test_default(client, setup, node_factory, mocker):
    table, workflow = setup

    mocker.patch("apps.nodes.bigquery.get_query_from_node", side_effect=raise_error)
    select_node = create_node(table, workflow, Node.Kind.SELECT, node_factory)
    r = client.get(f"/nodes/{select_node.id}/grid")
    assertOK(r)
    assertSelectorText(
        r,
        "p",
        "There seems to be an error with this node, try reconfiguring your workflow",
    )
