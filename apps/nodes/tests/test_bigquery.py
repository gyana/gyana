from datetime import date

import ibis
import pandas as pd
import pytest
from django.utils import timezone

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


def test_join_node(setup, engine):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()
    join_node = Node.objects.create(
        kind=Node.Kind.JOIN,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    join_node.parents.add(input_node)
    join_node.parents.add(second_input_node, through_defaults={"position": 1})
    join_column = join_node.join_columns.create(left_column="id", right_column="id")

    query = get_query_from_node(join_node)
    # Mocking the table conditionally requires a little bit more work
    # So we simply join the table with itself which leads to duplicate columns that
    # Are aliased
    left = engine.data.rename(lambda x: f"{x}_1")
    right = engine.data.rename(lambda x: f"{x}_2")
    expected = (
        left.join(right, left.id_1 == right.id_2, how="inner")
        .drop(["id_2"])
        .rename(id="id_1")
    )
    assert query.equals(expected)

    join_column.how = "outer"
    join_column.save()
    query = get_query_from_node(join_node)
    expected = left.join(right, left.id_1 == right.id_2, how="outer").relabel({})
    assert query.equals(expected)


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


def test_union_node(setup, engine):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()

    union_node = Node.objects.create(
        kind=Node.Kind.UNION,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    union_node.parents.add(input_node)
    union_node.parents.add(second_input_node, through_defaults={"position": 1})
    columns = engine.data.columns
    expected = engine.data.union(engine.data.projection(columns))
    assert get_query_from_node(union_node).equals(expected)

    union_node.union_distinct = True
    expected = engine.data.union(engine.data.projection(columns), distinct=True)
    assert get_query_from_node(union_node).equals(expected)


def test_union_node_casts_int_to_float(setup, engine):
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
    columns = engine.data.columns
    converted = engine.data.mutate(id=engine.data.id.cast("float"))
    expected = engine.data.mutate(id=engine.data.id.cast("float")).union(
        converted.projection(columns)
    )
    assert get_query_from_node(union_node).equals(expected)


def test_except_node(setup, engine):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()

    except_node = Node.objects.create(
        kind=Node.Kind.EXCEPT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    except_node.parents.add(input_node)
    except_node.parents.add(second_input_node, through_defaults={"position": 1})

    assert get_query_from_node(except_node).equals(engine.data.difference(engine.data))


def test_intersect_node(setup, engine):
    input_node, workflow = setup
    second_input_node = input_node.make_clone()

    intersect_node = Node.objects.create(
        kind=Node.Kind.INTERSECT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    intersect_node.parents.add(input_node)
    intersect_node.parents.add(second_input_node, through_defaults={"position": 1})

    assert get_query_from_node(intersect_node).equals(
        engine.data.intersect(engine.data)
    )


def test_sort_node(setup, engine):
    input_node, workflow = setup

    sort_node = Node.objects.create(
        kind=Node.Kind.SORT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    sort_node.parents.add(input_node)

    sort_node.sort_columns.create(column="id")

    assert get_query_from_node(sort_node).equals(engine.data.order_by("id"))

    sort_node.sort_columns.create(column="birthday", ascending=False)
    assert get_query_from_node(sort_node).equals(
        engine.data.order_by(["id", ibis.desc("birthday")])
    )


def test_limit_node(setup, engine):
    input_node, workflow = setup

    limit_node = Node.objects.create(
        kind=Node.Kind.LIMIT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    limit_node.parents.add(input_node)
    limited = engine.data.limit(100)
    assert get_query_from_node(limit_node).equals(limited[limited])

    limit_node.limit_offset = 50
    limit_node.limit_limit = 250
    limited = engine.data.limit(250, offset=50)
    assert get_query_from_node(limit_node).equals(limited[limited])


def test_filter_node(setup, engine):
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

    expected = engine.data[engine.data.athlete.notnull()]
    assert get_query_from_node(filter_node).equals(expected)

    filter_node.filters.create(
        column="birthday",
        datetime_predicate=DateRange.TODAY,
        type=Filter.Type.DATE,
    )
    assert get_query_from_node(filter_node).equals(
        expected[expected.birthday == date.today()]
    )


def test_edit_node(setup, engine):
    input_node, workflow = setup

    edit_node = Node.objects.create(
        kind=Node.Kind.EDIT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    edit_node.parents.add(input_node)

    edit_node.edit_columns.create(column="id", integer_function="isnull")

    assert get_query_from_node(edit_node).equals(
        engine.data.mutate(id=engine.data.id.isnull())
    )

    edit_node.edit_columns.create(column="athlete", string_function="upper")
    assert get_query_from_node(edit_node).equals(
        engine.data.mutate(
            id=engine.data.id.isnull(), athlete=engine.data.athlete.upper()
        )
    )


def test_add_node(setup, engine):
    input_node, workflow = setup

    add_node = Node.objects.create(
        kind=Node.Kind.ADD,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    add_node.parents.add(input_node)

    add_node.add_columns.create(column="id", integer_function="isnull", label="booly")
    assert get_query_from_node(add_node).equals(
        engine.data.mutate(booly=engine.data.id.isnull())
    )
    add_node.add_columns.create(
        column="athlete", string_function="upper", label="grand_athlete"
    )
    assert get_query_from_node(add_node).equals(
        engine.data.mutate(
            booly=engine.data.id.isnull(), grand_athlete=engine.data.athlete.upper()
        )
    )


def test_rename_node(setup, engine):
    input_node, workflow = setup

    rename_node = Node.objects.create(
        kind=Node.Kind.RENAME,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    rename_node.parents.add(input_node)

    rename_node.rename_columns.create(column="birthday", new_name="bd")
    assert get_query_from_node(rename_node).equals(
        engine.data.relabel(dict(birthday="bd"))
    )

    rename_node.rename_columns.create(column="id", new_name="identity")
    assert get_query_from_node(rename_node).equals(
        engine.data.relabel(dict(birthday="bd", id="identity"))
    )


def test_formula_node(setup, engine):
    input_node, workflow = setup

    formula_node = Node.objects.create(
        kind=Node.Kind.FORMULA,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    formula_node.parents.add(input_node)

    formula_node.formula_columns.create(formula="upper(athlete)", label="grand_athlete")

    assert get_query_from_node(formula_node).equals(
        engine.data.mutate(grand_athlete=engine.data.athlete.upper())
    )

    formula_node.formula_columns.create(formula="lower(athlete)", label="low_athlete")
    assert get_query_from_node(formula_node).equals(
        engine.data.mutate(
            grand_athlete=engine.data.athlete.upper(),
            low_athlete=engine.data.athlete.lower(),
        )
    )


def test_distinct_node(setup, engine):
    input_node, workflow = setup
    distinct_node = Node.objects.create(
        kind=Node.Kind.DISTINCT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    distinct_node.parents.add(input_node)

    distinct_node.columns.create(column="athlete")
    columns = [
        engine.data[column].any_value().name(column)
        for column in engine.data.columns
        if column != "athlete"
    ]
    assert get_query_from_node(distinct_node).equals(
        engine.data.group_by(["athlete"]).aggregate(columns)
    )

    distinct_node.columns.create(column="birthday")
    columns = [
        engine.data[column].any_value().name(column)
        for column in engine.data.columns
        if column not in ["athlete", "birthday"]
    ]
    assert get_query_from_node(distinct_node).equals(
        engine.data.group_by(["athlete", "birthday"]).aggregate(columns)
    )


def test_window_node(setup, engine):
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

    assert get_query_from_node(window_node).equals(
        engine.data.mutate(window=engine.data.athlete.count().over())
    )

    window.group_by = "birthday"
    window.save()
    assert get_query_from_node(window_node).equals(
        engine.data.mutate(
            window=engine.data.athlete.count().over(ibis.window(group_by="birthday"))
        )
    )

    window.order_by = "id"
    window.ascending = False
    window.save()
    birthday_window = engine.data.athlete.count().over(
        ibis.window(group_by="birthday", order_by=ibis.desc(engine.data.id))
    )
    assert get_query_from_node(window_node).equals(
        engine.data.mutate(window=birthday_window)
    )
    window_node.window_columns.create(
        column="id", function="count", group_by="athlete", label="door"
    )
    assert get_query_from_node(window_node).equals(
        engine.data.mutate(
            window=birthday_window,
            door=engine.data.id.count().over(ibis.window(group_by="athlete")),
        )
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


def test_convert_node(setup, engine):
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

    assert get_query_from_node(convert_node).equals(
        engine.data.cast(
            {
                "athlete": "int",
                "id": "string",
                "birthday": "timestamp",
            }
        )
    )
