import textwrap
from datetime import datetime

import ibis
import pandas as pd
import pytest
from django.utils import timezone
from ibis.backends.bigquery import Backend

from apps.columns.models import Column
from apps.filters.models import DateRange, Filter
from apps.nodes.engine import get_pivot_query, get_query_from_node, get_unpivot_query
from apps.nodes.models import Node
from apps.nodes.tests.mocks import DEFAULT_X_Y, INPUT_QUERY

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(
    logged_in_user,
    integration_factory,
    integration_table_factory,
    workflow_factory,
):

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


def test_input_node(setup, engine):
    input_node, _ = setup
    query = get_query_from_node(input_node)
    assert query.equals(engine.data)


def test_ouput_node(setup, engine):
    input_node, workflow = setup
    output_node = Node.objects.create(
        kind=Node.Kind.OUTPUT, workflow=workflow, **DEFAULT_X_Y
    )
    output_node.parents.add(input_node)
    query = get_query_from_node(output_node)

    assert query.equals(engine.data)


def test_select_node(setup, engine):
    input_node, workflow = setup
    select_node = Node.objects.create(
        kind=Node.Kind.SELECT, workflow=workflow, **DEFAULT_X_Y
    )
    select_node.parents.add(input_node)
    select_node.columns.add(
        Column(column="athlete"), Column(column="birthday"), bulk=False
    )

    query = get_query_from_node(select_node)
    assert query.equals(engine.data.projection(["athlete", "birthday"]))

    select_node.select_mode = "exclude"
    query = get_query_from_node(select_node)
    assert query.equals(engine.data.drop(["athlete", "birthday"]))


JOIN_QUERY = """\
WITH t0 AS (
  SELECT
    t3.`id` AS `id_2`,
    t3.`athlete` AS `athlete_2`,
    t3.`birthday` AS `birthday_2`,
    t3.`when` AS `when_2`,
    t3.`lunch` AS `lunch_2`,
    t3.`medals` AS `medals_2`,
    t3.`stars` AS `stars_2`,
    t3.`is_nice` AS `is_nice_2`,
    t3.`biography` AS `biography_2`
  FROM `project.dataset`.table AS t3
), t1 AS (
  SELECT
    t3.`id` AS `id_1`,
    t3.`athlete` AS `athlete_1`,
    t3.`birthday` AS `birthday_1`,
    t3.`when` AS `when_1`,
    t3.`lunch` AS `lunch_1`,
    t3.`medals` AS `medals_1`,
    t3.`stars` AS `stars_1`,
    t3.`is_nice` AS `is_nice_1`,
    t3.`biography` AS `biography_1`
  FROM `project.dataset`.table AS t3
)
SELECT
  t2.`id_1` AS `id`,
  t2.`athlete_1`,
  t2.`birthday_1`,
  t2.`when_1`,
  t2.`lunch_1`,
  t2.`medals_1`,
  t2.`stars_1`,
  t2.`is_nice_1`,
  t2.`biography_1`,
  t2.`athlete_2`,
  t2.`birthday_2`,
  t2.`when_2`,
  t2.`lunch_2`,
  t2.`medals_2`,
  t2.`stars_2`,
  t2.`is_nice_2`,
  t2.`biography_2`
FROM (
  SELECT
    `id_1`,
    `athlete_1`,
    `birthday_1`,
    `when_1`,
    `lunch_1`,
    `medals_1`,
    `stars_1`,
    `is_nice_1`,
    `biography_1`,
    `athlete_2`,
    `birthday_2`,
    `when_2`,
    `lunch_2`,
    `medals_2`,
    `stars_2`,
    `is_nice_2`,
    `biography_2`
  FROM t1
  INNER JOIN t0
    ON t1.`id_1` = t0.`id_2`
) AS t2\
"""


def test_join_node(setup):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()
    join_node = Node.objects.create(
        kind=Node.Kind.JOIN,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    join_node.parents.add(input_node)
    join_node.parents.add(second_input_node, through_defaults={"position": 1})
    join_node.join_columns.create(left_column="id", right_column="id")

    query = get_query_from_node(join_node)
    # Mocking the table conditionally requires a little bit more work
    # So we simply join the table with itself which leads to duplicate columns that
    # Are aliased
    assert query.compile() == JOIN_QUERY

    join_node.join_how = "outer"
    query = get_query_from_node(join_node)
    # TODO: Weird that this doesnt need any change?
    assert query.compile() == JOIN_QUERY


def test_aggregation_node(setup, engine):
    input_node, workflow = setup
    aggregation_node = Node.objects.create(
        kind=Node.Kind.AGGREGATION,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    aggregation_node.parents.add(input_node)
    assert get_query_from_node(aggregation_node).equals(
        engine.data.agg(count=ibis._.count())
    )

    aggregation_node.aggregations.create(column="id", function="sum")
    assert get_query_from_node(aggregation_node).equals(
        engine.data.aggregate(engine.data.id.sum().name("id"))
    )

    aggregation_node.columns.create(column="birthday")
    assert get_query_from_node(aggregation_node).equals(
        engine.data.group_by(["birthday"]).aggregate(engine.data.id.sum().name("id"))
    )

    aggregation_node.columns.create(column="athlete")
    assert get_query_from_node(aggregation_node).equals(
        engine.data.group_by(["birthday", "athlete"]).aggregate(
            engine.data.id.sum().name("id")
        )
    )


UNION_QUERY = """\
SELECT
  t0.`id`,
  t0.`athlete`,
  t0.`birthday`,
  t0.`when`,
  t0.`lunch`,
  t0.`medals`,
  t0.`stars`,
  t0.`is_nice`,
  t0.`biography`
FROM (
  WITH t1 AS (
    SELECT
      t2.`id`,
      t2.`athlete`,
      t2.`birthday`,
      t2.`when`,
      t2.`lunch`,
      t2.`medals`,
      t2.`stars`,
      t2.`is_nice`,
      t2.`biography`
    FROM `project.dataset`.table AS t2
  )
  SELECT
    t2.*
  FROM `project.dataset`.table AS t2
  UNION ALL
  SELECT
    *
  FROM t1
) AS t0\
"""


EXCEPT_QUERY = """\
SELECT
  t0.`id`,
  t0.`athlete`,
  t0.`birthday`,
  t0.`when`,
  t0.`lunch`,
  t0.`medals`,
  t0.`stars`,
  t0.`is_nice`,
  t0.`biography`
FROM (
  SELECT
    t1.*
  FROM `project.dataset`.table AS t1
  EXCEPT DISTINCT
  SELECT
    t1.*
  FROM `project.dataset`.table AS t1
) AS t0\
"""


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


UNION_CAST_QUERY = """\
WITH t0 AS (
  SELECT
    CAST(t2.`id` AS FLOAT64) AS `id`,
    t2.`athlete`,
    t2.`birthday`,
    t2.`when`,
    t2.`lunch`,
    t2.`medals`,
    t2.`stars`,
    t2.`is_nice`,
    t2.`biography`
  FROM `project.dataset`.table AS t2
)
SELECT
  t1.`id`,
  t1.`athlete`,
  t1.`birthday`,
  t1.`when`,
  t1.`lunch`,
  t1.`medals`,
  t1.`stars`,
  t1.`is_nice`,
  t1.`biography`
FROM (
  WITH t0 AS (
    SELECT
      CAST(t2.`id` AS FLOAT64) AS `id`,
      t2.`athlete`,
      t2.`birthday`,
      t2.`when`,
      t2.`lunch`,
      t2.`medals`,
      t2.`stars`,
      t2.`is_nice`,
      t2.`biography`
    FROM `project.dataset`.table AS t2
  ), t2 AS (
    SELECT
      t0.`id`,
      t0.`athlete`,
      t0.`birthday`,
      t0.`when`,
      t0.`lunch`,
      t0.`medals`,
      t0.`stars`,
      t0.`is_nice`,
      t0.`biography`
    FROM t0
  )
  SELECT
    *
  FROM t0
  UNION ALL
  SELECT
    *
  FROM t2
) AS t1\
"""


def test_union_node_casts_int_to_float(setup):
    input_node, workflow = setup

    union_node = Node.objects.create(
        kind=Node.Kind.UNION,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    convert_node = Node.objects.create(
        kind=Node.Kind.CONVERT, workflow=workflow, **DEFAULT_X_Y
    )
    convert_node.parents.add(input_node)
    convert_node.convert_columns.create(column="id", target_type="float")

    union_node.parents.add(input_node)
    union_node.parents.add(convert_node, through_defaults={"position": 1})

    assert get_query_from_node(union_node).compile() == UNION_CAST_QUERY


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
    sort_query = f"{INPUT_QUERY}\nORDER BY\n  t0.`id` ASC"
    assert get_query_from_node(sort_node).compile() == sort_query

    sort_node.sort_columns.create(column="birthday", ascending=False)
    assert (
        get_query_from_node(sort_node).compile()
        == sort_query + ",\n  t0.`birthday` DESC"
    )


def test_limit_node(setup):
    input_node, workflow = setup

    limit_node = Node.objects.create(
        kind=Node.Kind.LIMIT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    limit_node.parents.add(input_node)

    limit_query = (
        f"SELECT\n  t0.*"
        f"\nFROM (\n{textwrap.indent(INPUT_QUERY.replace('t0', 't1'), '  ')}"
        f"\n  LIMIT 100\n) AS t0"
    )
    assert get_query_from_node(limit_node).compile() == limit_query

    limit_node.limit_offset = 50
    limit_node.limit_limit = 250

    assert get_query_from_node(limit_node).compile() == limit_query.replace(
        "LIMIT 100", "LIMIT 250\n  OFFSET 50"
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
        == f"{INPUT_QUERY}\nWHERE\n  NOT t0.`athlete` IS NULL"
    )

    filter_node.filters.create(
        column="birthday",
        datetime_predicate=DateRange.TODAY,
        type=Filter.Type.DATE,
    )
    assert get_query_from_node(filter_node).compile() == (
        f"{INPUT_QUERY}\nWHERE\n  (\n    NOT t0.`athlete` IS NULL\n  ) AND (\n    "
        f"t0.`birthday` = CAST('{datetime.now().strftime('%Y-%m-%d')}' AS DATE)\n  )"
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
    limit_query = INPUT_QUERY.replace(
        "t0.*",
        "t0.`id` IS NULL AS `id`,\n  t0.`athlete`,\n  t0.`birthday`,\n  t0.`when`,\n  t0.`lunch`,\n  t0.`medals`,\n  t0.`stars`,\n  t0.`is_nice`,\n  t0.`biography`",
    )
    assert get_query_from_node(edit_node).compile() == limit_query

    edit_node.edit_columns.create(column="athlete", string_function="upper")
    assert get_query_from_node(edit_node).compile() == limit_query.replace(
        "t0.`athlete`",
        "upper(t0.`athlete`) AS `athlete`",
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
        "t0.*", "t0.*,\n  t0.`id` IS NULL AS `booly`"
    )

    add_node.add_columns.create(
        column="athlete", string_function="upper", label="grand_athlete"
    )
    assert get_query_from_node(add_node).compile() == INPUT_QUERY.replace(
        "t0.*",
        "t0.*,\n  t0.`id` IS NULL AS `booly`,\n  upper(t0.`athlete`) AS `grand_athlete`",
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
    rename_query = INPUT_QUERY.replace(
        "t0.*",
        "t0.`id`,\n  t0.`athlete`,\n  t0.`birthday` AS `bd`,\n  t0.`when`,\n  t0.`lunch`,\n  t0.`medals`,\n  t0.`stars`,\n  t0.`is_nice`,\n  t0.`biography`",
    )
    assert get_query_from_node(rename_node).compile() == rename_query

    rename_node.rename_columns.create(column="id", new_name="identity")
    assert get_query_from_node(rename_node).compile() == rename_query.replace(
        "t0.`id`", "t0.`id` AS `identity`"
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
    formula_query = INPUT_QUERY.replace(
        "t0.*", "t0.*,\n  upper(t0.`athlete`) AS `grand_athlete`"
    )
    assert get_query_from_node(formula_node).compile() == formula_query

    formula_node.formula_columns.create(formula="lower(athlete)", label="low_athlete")
    assert get_query_from_node(formula_node).compile() == INPUT_QUERY.replace(
        "t0.*",
        "t0.*,\n  upper(t0.`athlete`) AS `grand_athlete`,\n  lower(t0.`athlete`) AS `low_athlete`",
    )


DISTINCT_COLUMNS = """t0.`athlete`,
  ANY_VALUE(t0.`id`) AS `id`,
  ANY_VALUE(t0.`birthday`) AS `birthday`,
  ANY_VALUE(t0.`when`) AS `when`,
  ANY_VALUE(t0.`lunch`) AS `lunch`,
  ANY_VALUE(t0.`medals`) AS `medals`,
  ANY_VALUE(t0.`stars`) AS `stars`,
  ANY_VALUE(t0.`is_nice`) AS `is_nice`,
  ANY_VALUE(t0.`biography`) AS `biography`\
"""


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
        INPUT_QUERY.replace("t0.*", DISTINCT_COLUMNS) + "\nGROUP BY\n  1"
    )

    distinct_node.columns.create(column="birthday")
    assert get_query_from_node(distinct_node).compile() == (
        INPUT_QUERY.replace(
            "t0.*",
            DISTINCT_COLUMNS.replace(
                "t0.`athlete`,", "t0.`athlete`,\n  t0.`birthday`,"
            ).replace("  ANY_VALUE(t0.`birthday`) AS `birthday`,\n", ""),
        )
        + "\nGROUP BY\n  1,\n  2"
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
        "t0.*", "t0.*,\n  count(t0.`athlete`) OVER () AS `window`"
    )

    window.group_by = "birthday"
    window.save()
    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "t0.*",
        "t0.*,\n  count(t0.`athlete`) OVER (PARTITION BY t0.`birthday`) AS `window`",
    )

    window.order_by = "id"
    window.ascending = False
    window.save()
    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "t0.*",
        "t0.*,\n  count(t0.`athlete`) OVER (PARTITION BY t0.`birthday` ORDER BY t0.`id` DESC) AS `window`",
    )

    window_node.window_columns.create(
        column="id", function="count", group_by="athlete", label="door"
    )
    assert get_query_from_node(window_node).compile() == INPUT_QUERY.replace(
        "t0.*",
        """t0.*,
  count(t0.`athlete`) OVER (PARTITION BY t0.`birthday` ORDER BY t0.`id` DESC) AS `window`,
  count(t0.`id`) OVER (PARTITION BY t0.`athlete`) AS `door`""",
    )


def test_pivot_node(setup, mocker, engine):
    input_node, workflow = setup
    pivot_node = Node.objects.create(
        kind=Node.Kind.PIVOT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    pivot_node.parents.add(input_node)

    engine.set_data(pd.DataFrame({"athlete": ["Usain Bolt", "Sakura Yosozumi"]}))
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
        "  t0.*",
        """\
  CAST(t0.`id` AS STRING) AS `id`,
  CAST(t0.`athlete` AS INT64) AS `athlete`,
  CAST(t0.`birthday` AS DATETIME) AS `birthday`,
  t0.`when`,\n  t0.`lunch`,\n  t0.`medals`,\n  t0.`stars`,\n  t0.`is_nice`,\n  t0.`biography`\
""",
    )
