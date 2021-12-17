import re
import textwrap
from datetime import date, datetime
from functools import lru_cache
from unittest import mock
from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest
from django.utils import timezone
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable

from apps.base import clients
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import TABLE_NAME, PickableMock
from apps.columns.models import Column
from apps.filters.models import DateRange, Filter
from apps.nodes._sentiment_utils import (
    DELIMITER,
    SENTIMENT_COLUMN_NAME,
    TEXT_COLUMN_NAME,
)
from apps.nodes.bigquery import (
    NodeResultNone,
    get_pivot_query,
    get_query_from_node,
    get_unpivot_query,
)
from apps.nodes.models import Node
from apps.teams.models import CreditTransaction

pytestmark = pytest.mark.django_db

INPUT_QUERY = f"SELECT *\nFROM `{TABLE_NAME}`"
DEFAULT_X_Y = {"x": 0, "y": 0}

USAIN = "Usain Bolt"
SAKURA = "Sakura Yosozumi"
INPUT_DATA = [
    {
        "id": 1,
        "athlete": USAIN,
        "birthday": date(year=1986, month=8, day=21),
    },
    {
        "id": 2,
        "athlete": SAKURA,
        "birthday": date(year=2002, month=3, day=15),
    },
]

DISTINCT_QUERY = "SELECT t0.*\nFROM (\n  SELECT DISTINCT `athlete` AS `text`\n  FROM `project.dataset.table`\n) t0\nWHERE t0.`text` IS NOT NULL"


def mock_bq_client_data(bigquery):
    def side_effect(query, **kwargs):
        mock = PickableMock()

        if query == DISTINCT_QUERY:
            mock.rows_dict = [{"text": row["athlete"]} for row in INPUT_DATA]
            mock.total_rows = len(INPUT_DATA)
        elif "EXCEPT DISTINCT" in query:
            mock.rows_dict = []
            mock.total_rows = 0
        else:
            mock.rows_dict = INPUT_DATA
            mock.total_rows = len(INPUT_DATA)
        return mock

    def result(query, **kwargs):
        mock = PickableMock()

        if query == DISTINCT_QUERY:
            mock.result = Mock(
                return_value=[{"text": row["athlete"]} for row in INPUT_DATA]
            )
            mock.total_rows = len(INPUT_DATA)
        elif "EXCEPT DISTINCT" in query:
            mock.result = Mock(return_value=[])
            mock.total_rows = 0
        else:
            mock.result = Mock(return_value=INPUT_DATA)
            mock.total_rows = len(INPUT_DATA)

        return mock

    bigquery.query = Mock(side_effect=result)
    bigquery.get_query_results = Mock(side_effect=side_effect)


def mock_bq_client_schema(bigquery):
    def side_effect(table, **kwargs):
        if table.split(".")[-1].split("_")[0] in [
            "cache",
            "intermediate",
        ]:
            schema = [
                SchemaField(TEXT_COLUMN_NAME, "string"),
                SchemaField(SENTIMENT_COLUMN_NAME, "float"),
            ]
        else:
            schema = [
                SchemaField(column, type_.name)
                for column, type_ in TABLE.schema().items()
            ][:3]
        return BqTable(
            table,
            schema=schema,
        )

    bigquery.get_table = MagicMock(side_effect=side_effect)


@pytest.fixture
def setup(
    logged_in_user,
    bigquery,
    integration_factory,
    integration_table_factory,
    workflow_factory,
):
    mock_bq_client_schema(bigquery)
    mock_bq_client_data(bigquery)

    team = logged_in_user.teams.first()
    workflow = workflow_factory(project__team=team)
    integration = integration_factory(project=workflow.project)
    table = integration_table_factory(
        project=workflow.project,
        integration=integration,
    )

    return (
        Node.objects.create(
            kind=Node.Kind.INPUT,
            input_table=table,
            workflow=workflow,
            data_updated=timezone.now(),
            **DEFAULT_X_Y,
        ),
        workflow,
    )


def test_input_node(setup):
    input_node, _ = setup
    query = get_query_from_node(input_node)
    assert query.compile() == INPUT_QUERY


def test_ouput_node(setup):
    input_node, workflow = setup
    output_node = Node.objects.create(
        kind=Node.Kind.OUTPUT, workflow=workflow, **DEFAULT_X_Y
    )
    output_node.parents.add(input_node)
    query = get_query_from_node(output_node)

    assert query.compile() == INPUT_QUERY


def test_select_node(setup):
    input_node, workflow = setup
    select_node = Node.objects.create(
        kind=Node.Kind.SELECT, workflow=workflow, **DEFAULT_X_Y
    )
    select_node.parents.add(input_node)
    select_node.columns.add(
        Column(column="athlete"), Column(column="birthday"), bulk=False
    )

    query = get_query_from_node(select_node)
    assert query.compile() == INPUT_QUERY.replace("*", "`athlete`, `birthday`")

    select_node.select_mode = "exclude"
    query = get_query_from_node(select_node)
    assert query.compile() == INPUT_QUERY.replace("*", "`id`")


def test_join_node(setup):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()
    join_node = Node.objects.create(
        kind=Node.Kind.JOIN,
        workflow=workflow,
        **DEFAULT_X_Y,
        join_left="id",
        join_right="id",
    )
    join_node.parents.add(input_node)
    join_node.parents.add(second_input_node, through_defaults={"position": 1})

    query = get_query_from_node(join_node)
    # Mocking the table conditionally requires a little bit more work
    # So we simply join the table with itself which leads to duplicate columns that
    # Are aliased
    join_query = "SELECT `id_left` AS `id`, `athlete_left`, `birthday_left`, `athlete_right`,\n       `birthday_right`\nFROM (\n  SELECT *\n  FROM (\n    SELECT `id` AS `id_left`, `athlete` AS `athlete_left`,\n           `birthday` AS `birthday_left`\n    FROM `project.dataset.table`\n  ) t1\n    INNER JOIN (\n      SELECT `id` AS `id_right`, `athlete` AS `athlete_right`,\n             `birthday` AS `birthday_right`\n      FROM `project.dataset.table`\n    ) t2\n      ON t1.`id_left` = t2.`id_right`\n) t0"
    assert query.compile() == join_query

    join_node.join_how = "outer"
    query = get_query_from_node(join_node)
    assert (
        query.compile()
        == """\
SELECT *
FROM (
  SELECT `id` AS `id_left`, `athlete` AS `athlete_left`,
         `birthday` AS `birthday_left`
  FROM `project.dataset.table`
) t0
  FULL OUTER JOIN (
    SELECT `id` AS `id_right`, `athlete` AS `athlete_right`,
           `birthday` AS `birthday_right`
    FROM `project.dataset.table`
  ) t1
    ON t0.`id_left` = t1.`id_right`"""
    )


def test_aggregation_node(setup):
    input_node, workflow = setup
    aggregation_node = Node.objects.create(
        kind=Node.Kind.AGGREGATION,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    aggregation_node.parents.add(input_node)

    assert get_query_from_node(aggregation_node).compile() == INPUT_QUERY.replace(
        "*", "count(*) AS `count`"
    )

    aggregation_node.aggregations.create(column="id", function="sum")
    assert get_query_from_node(aggregation_node).compile() == INPUT_QUERY.replace(
        "*", "sum(`id`) AS `id`"
    )

    aggregation_node.columns.create(column="birthday")
    assert (
        get_query_from_node(aggregation_node).compile()
        == INPUT_QUERY.replace("*", "`birthday`, sum(`id`) AS `id`") + "\nGROUP BY 1"
    )

    aggregation_node.columns.create(column="athlete")
    assert (
        get_query_from_node(aggregation_node).compile()
        == INPUT_QUERY.replace("*", "`birthday`, `athlete`, sum(`id`) AS `id`")
        + "\nGROUP BY 1, 2"
    )


UNION_QUERY = (
    f"SELECT `id`, `athlete`, `birthday`"
    f"\nFROM (\n{textwrap.indent(INPUT_QUERY, '  ')}\n  UNION ALL"
    f"\n{textwrap.indent(INPUT_QUERY.replace('*', '`id`, `athlete`, `birthday`'), '  ')}\n) t0"
)


EXCEPT_QUERY = (
    f"SELECT `id`, `athlete`, `birthday`"
    f"\nFROM (\n{textwrap.indent(INPUT_QUERY, '  ')}\n  EXCEPT DISTINCT"
    f"\n{textwrap.indent(INPUT_QUERY, '  ')}\n) t0"
)


def test_union_node(setup):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()

    union_node = Node.objects.create(
        kind=Node.Kind.UNION,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    union_node.parents.add(input_node)
    union_node.parents.add(second_input_node, through_defaults={"position": 1})

    assert get_query_from_node(union_node).compile() == UNION_QUERY

    union_node.union_distinct = True
    assert get_query_from_node(union_node).compile() == UNION_QUERY.replace(
        "UNION ALL", "UNION DISTINCT"
    )


def test_except_node(setup):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()

    except_node = Node.objects.create(
        kind=Node.Kind.EXCEPT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    except_node.parents.add(input_node)
    except_node.parents.add(second_input_node, through_defaults={"position": 1})

    assert get_query_from_node(except_node).compile() == EXCEPT_QUERY


def test_intersect_node(setup):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()

    intersect_node = Node.objects.create(
        kind=Node.Kind.INTERSECT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    intersect_node.parents.add(input_node)
    intersect_node.parents.add(second_input_node, through_defaults={"position": 1})

    assert get_query_from_node(intersect_node).compile() == EXCEPT_QUERY.replace(
        "EXCEPT DISTINCT", "INTERSECT DISTINCT"
    )


def test_sort_node(setup):
    input_node, workflow = setup

    sort_node = Node.objects.create(
        kind=Node.Kind.SORT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    sort_node.parents.add(input_node)

    sort_node.sort_columns.create(column="id")
    sort_query = f"{INPUT_QUERY}\nORDER BY `id`"
    assert get_query_from_node(sort_node).compile() == sort_query

    sort_node.sort_columns.create(column="birthday", ascending=False)
    assert get_query_from_node(sort_node).compile() == sort_query + ", `birthday` DESC"


def test_limit_node(setup):
    input_node, workflow = setup

    limit_node = Node.objects.create(
        kind=Node.Kind.LIMIT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    limit_node.parents.add(input_node)

    limit_query = (
        f"SELECT `id`, `athlete`, `birthday`"
        f"\nFROM (\n{textwrap.indent(INPUT_QUERY, '  ')}"
        f"\n  LIMIT 100\n) t0"
    )
    assert get_query_from_node(limit_node).compile() == limit_query

    limit_node.limit_offset = 50
    limit_node.limit_limit = 250

    assert get_query_from_node(limit_node).compile() == limit_query.replace(
        "LIMIT 100", "LIMIT 250 OFFSET 50"
    )


def test_filter_node(setup):
    input_node, workflow = setup

    filter_node = Node.objects.create(
        kind=Node.Kind.FILTER,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    filter_node.parents.add(input_node)
    filter_node.filters.create(
        column="athlete",
        string_predicate=Filter.StringPredicate.NOTNULL,
        type=Filter.Type.STRING,
    )

    assert (
        get_query_from_node(filter_node).compile()
        == f"{INPUT_QUERY}\nWHERE `athlete` IS NOT NULL"
    )

    filter_node.filters.create(
        column="birthday",
        datetime_predicate=DateRange.TODAY,
        type=Filter.Type.DATE,
    )
    assert get_query_from_node(filter_node).compile() == (
        f"{INPUT_QUERY}\nWHERE (`athlete` IS NOT NULL) AND\n      "
        f"(`birthday` = DATE '{datetime.now().strftime('%Y-%m-%d')}')"
    )


def test_edit_node(setup):
    input_node, workflow = setup

    edit_node = Node.objects.create(
        kind=Node.Kind.EDIT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    edit_node.parents.add(input_node)

    edit_node.edit_columns.create(column="id", integer_function="isnull")
    assert get_query_from_node(edit_node).compile() == INPUT_QUERY.replace(
        "*", "`id` IS NULL AS `id`, `athlete`, `birthday`"
    )

    edit_node.edit_columns.create(column="athlete", string_function="upper")
    assert get_query_from_node(edit_node).compile() == INPUT_QUERY.replace(
        "*", "`id` IS NULL AS `id`, upper(`athlete`) AS `athlete`, `birthday`"
    )


def test_add_node(setup):
    input_node, workflow = setup

    add_node = Node.objects.create(
        kind=Node.Kind.ADD,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    add_node.parents.add(input_node)

    add_node.add_columns.create(column="id", integer_function="isnull", label="booly")
    assert get_query_from_node(add_node).compile() == INPUT_QUERY.replace(
        "*", "*, `id` IS NULL AS `booly`"
    )

    add_node.add_columns.create(
        column="athlete", string_function="upper", label="grand_athlete"
    )
    assert get_query_from_node(add_node).compile() == INPUT_QUERY.replace(
        "*", "*, `id` IS NULL AS `booly`, upper(`athlete`) AS `grand_athlete`"
    )


def test_rename_node(setup):
    input_node, workflow = setup

    rename_node = Node.objects.create(
        kind=Node.Kind.RENAME,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    rename_node.parents.add(input_node)

    rename_node.rename_columns.create(column="birthday", new_name="bd")
    assert get_query_from_node(rename_node).compile() == INPUT_QUERY.replace(
        "*", "`id`, `athlete`, `birthday` AS `bd`"
    )

    rename_node.rename_columns.create(column="id", new_name="identity")
    assert get_query_from_node(rename_node).compile() == INPUT_QUERY.replace(
        "*", "`id` AS `identity`, `athlete`, `birthday` AS `bd`"
    )


def test_formula_node(setup):
    input_node, workflow = setup

    formula_node = Node.objects.create(
        kind=Node.Kind.FORMULA,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    formula_node.parents.add(input_node)

    formula_node.formula_columns.create(formula="upper(athlete)", label="grand_athlete")
    assert get_query_from_node(formula_node).compile() == INPUT_QUERY.replace(
        "*", "*, upper(`athlete`) AS `grand_athlete`"
    )

    formula_node.formula_columns.create(formula="lower(athlete)", label="low_athlete")
    assert get_query_from_node(formula_node).compile() == INPUT_QUERY.replace(
        "*",
        "*, upper(`athlete`) AS `grand_athlete`,\n       lower(`athlete`) AS `low_athlete`",
    )


def test_distinct_node(setup):
    input_node, workflow = setup
    distinct_node = Node.objects.create(
        kind=Node.Kind.DISTINCT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    distinct_node.parents.add(input_node)

    distinct_node.columns.create(column="athlete")

    assert get_query_from_node(distinct_node).compile() == (
        INPUT_QUERY.replace(
            "*",
            "`athlete`, ANY_VALUE(`id`) AS `id`,\n       ANY_VALUE(`birthday`) AS `birthday`",
        )
        + "\nGROUP BY 1"
    )

    distinct_node.columns.create(column="birthday")
    assert get_query_from_node(distinct_node).compile() == (
        INPUT_QUERY.replace(
            "*",
            "`athlete`, `birthday`, ANY_VALUE(`id`) AS `id`",
        )
        + "\nGROUP BY 1, 2"
    )


def test_window_node(setup):
    input_node, workflow = setup
    window_node = Node.objects.create(
        kind=Node.Kind.WINDOW,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    window_node.parents.add(input_node)

    window = window_node.window_columns.create(
        column="athlete", function="count", label="window"
    )

    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "*", "*, count(`athlete`) OVER () AS `window`"
    )

    window.group_by = "birthday"
    window.save()
    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "*", "*, count(`athlete`) OVER (PARTITION BY `birthday`) AS `window`"
    )

    window.order_by = "id"
    window.ascending = False
    window.save()
    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "*",
        "*,\n       count(`athlete`) OVER (PARTITION BY `birthday` ORDER BY `id`) AS `window`",
    )

    window_node.window_columns.create(
        column="id", function="count", group_by="athlete", label="door"
    )
    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "*",
        """*,
       count(`athlete`) OVER (PARTITION BY `birthday` ORDER BY `id`) AS `window`,
       count(`id`) OVER (PARTITION BY `athlete`) AS `door`""",
    )


def test_pivot_node(setup):
    input_node, workflow = setup
    pivot_node = Node.objects.create(
        kind=Node.Kind.PIVOT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    pivot_node.parents.add(input_node)

    pivot_node.pivot_column = "athlete"
    pivot_node.pivot_index = "id"
    pivot_node.pivot_aggregation = "sum"
    pivot_node.pivot_value = "birthday"

    # We only want to check that the right query is formed
    query = get_pivot_query.__wrapped__(pivot_node, get_query_from_node(input_node))
    assert query == (
        f"SELECT * FROM  (SELECT id, athlete, birthday FROM "
        f"({INPUT_QUERY}))  PIVOT(sum(birthday)      "
        f'FOR athlete IN ("Usain Bolt" Usain_Bolt, "Sakura Yosozumi" Sakura_Yosozumi)  )'
    )


def test_unpivot_node(setup):
    input_node, workflow = setup
    unpivot_node = Node.objects.create(
        kind=Node.Kind.UNPIVOT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    unpivot_node.parents.add(input_node)

    unpivot_node.unpivot_column = "category"
    unpivot_node.unpivot_value = "value"
    unpivot_node.columns.create(column="athlete")

    # We only want to check that the right query is formed
    query = get_unpivot_query.__wrapped__(unpivot_node, get_query_from_node(input_node))
    assert query == (
        f"SELECT category, value FROM ({INPUT_QUERY})"
        f" UNPIVOT(value FOR category IN (athlete))"
    )

    unpivot_node.columns.create(column="birthday")
    unpivot_node.secondary_columns.create(column="id")
    assert get_unpivot_query.__wrapped__(
        unpivot_node, get_query_from_node(input_node)
    ) == (
        f"SELECT id, category, value FROM ({INPUT_QUERY})"
        f" UNPIVOT(value FOR category IN (athlete, birthday))"
    )


POSITIVE_SCORE = +0.9
NEGATIVE_SCORE = -0.9

SENTIMENT_LOOKUP = {SAKURA: POSITIVE_SCORE, USAIN: NEGATIVE_SCORE}


# cache as creating mocks is expensive
@lru_cache(len(SENTIMENT_LOOKUP))
def score_to_sentence_mock(sentence_text: str):
    """Mocks a sentence to place inside an AnalyzeSentimentResponse"""
    sentence = mock.MagicMock()
    sentence.text.content = sentence_text
    sentence.sentiment.score = SENTIMENT_LOOKUP[sentence_text]
    return sentence


def mock_gcp_analyze_sentiment(text, _):
    """Mocks the AnalyzeSentimentResponse sent back from GCP"""
    mocked = mock.MagicMock()

    # covers the scalar case too as scalars are sent over as a single-row column
    mocked.sentences = [score_to_sentence_mock(x) for x in text.split(DELIMITER)]

    return mocked


SENTIMENT_QUERY = "SELECT \\*\nFROM `project.cypress_team_.*_tables\\..*`"


def _create_sentiment_node(input_node, workflow):
    node = Node.objects.create(
        kind=Node.Kind.SENTIMENT,
        workflow=workflow,
        **DEFAULT_X_Y,
        sentiment_column="athlete",
        data_updated=timezone.now(),
    )
    node.parents.add(input_node)
    return node


def test_sentiment_query(mocker, logged_in_user, setup):
    input_node, workflow = setup
    sentiment_node = _create_sentiment_node(input_node, workflow)
    team = logged_in_user.teams.first()

    with pytest.raises(NodeResultNone) as err:
        get_query_from_node(sentiment_node)

    # Should error and not charge any credits
    assert sentiment_node.error == "credit_exception"
    assert sentiment_node.uses_credits == len(INPUT_DATA)
    assert team.current_credit_balance == 0

    # Confirm credit usage
    sentiment_node.credit_use_confirmed = timezone.now()
    sentiment_node.credit_confirmed_user = logged_in_user
    sentiment_node.save()

    mocker.patch(
        target="apps.nodes._sentiment_utils._gcp_analyze_sentiment",
        side_effect=mock_gcp_analyze_sentiment,
    )
    mocker.patch(
        "apps.nodes._sentiment_utils.LanguageServiceClient",
        side_effect=mock.MagicMock,
    )
    query = get_query_from_node(sentiment_node)
    assert re.match(re.compile(SENTIMENT_QUERY), query.compile())

    # Should have charged credits and uploaded the right dataframe
    uploaded_df = clients.bigquery().load_table_from_dataframe.call_args.args[0]
    assert team.current_credit_balance == 2
    pd._testing.assert_frame_equal(
        uploaded_df,
        pd.DataFrame(
            {"text": [USAIN, SAKURA], "sentiment": [NEGATIVE_SCORE, POSITIVE_SCORE]}
        ),
    )

    # Fake update to input node
    # It still shouldnt charge any credits
    input_node.data_updated = timezone.now()
    input_node.save()
    # Need to refresh object because it has new props updated in the celery task
    sentiment_node.refresh_from_db()

    query = get_query_from_node(sentiment_node)
    assert re.match(re.compile(SENTIMENT_QUERY), query.compile())
    assert team.current_credit_balance == 2


def test_convert_node(setup):
    input_node, workflow = setup
    convert_node = Node.objects.create(
        kind=Node.Kind.CONVERT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    convert_node.parents.add(input_node)

    for column, target_type in [
        ("athlete", "int"),
        ("id", "text"),
        ("birthday", "timestamp"),
    ]:
        convert_node.convert_columns.create(column=column, target_type=target_type)

    assert get_query_from_node(convert_node).compile() == INPUT_QUERY.replace(
        "*",
        """\
CAST(`id` AS STRING) AS `id`, \
CAST(`athlete` AS INT64) AS `athlete`,
       CAST(`birthday` AS TIMESTAMP) AS `birthday`""",
    )


def test_sentiment_query_out_of_credits(logged_in_user, setup):
    input_node, workflow = setup
    sentiment_node = _create_sentiment_node(input_node, workflow)
    team = logged_in_user.teams.first()

    # Add credits so that operation would consume too many credits
    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.INCREASE,
        amount=99,
        user=logged_in_user,
    )
    with pytest.raises(NodeResultNone) as err:
        get_query_from_node(sentiment_node)

    assert sentiment_node.error == "out_of_credits_exception"
