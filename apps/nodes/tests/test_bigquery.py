import pytest
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.columns.models import Column
from apps.integrations.models import Integration
from apps.nodes.bigquery import get_query_from_node
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.tables.models import Table
from apps.workflows.models import Workflow

pytestmark = pytest.mark.django_db

TABLE_NAME = "gyana-1511894275181.dataset.table"
INPUT_QUERY = f"SELECT *\nFROM `{TABLE_NAME}`"
DEFAULT_X_Y = {"x": 0, "y": 0}


def setup_input_node(logged_in_user, bigquery_client):
    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)
    integration = Integration.objects.create(
        project=project, kind=Integration.Kind.UPLOAD, name="store_info", ready=True
    )
    table = Table.objects.create(
        project=project,
        integration=integration,
        source=Table.Source.INTEGRATION,
        bq_table="table",
        bq_dataset="dataset",
    )
    workflow = Workflow.objects.create(project=project)

    mock_bq_client_with_schema(
        bigquery_client,
        [(column, type_.name) for column, type_ in TABLE.schema().items()][:3],
    )
    return (
        Node.objects.create(
            kind=Node.Kind.INPUT, input_table=table, workflow=workflow, **DEFAULT_X_Y
        ),
        workflow,
    )


def test_input_node(logged_in_user, bigquery_client):
    input_node, _ = setup_input_node(logged_in_user, bigquery_client)
    query = get_query_from_node(input_node)
    assert query.compile() == INPUT_QUERY


def test_ouput_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
    output_node = Node.objects.create(
        kind=Node.Kind.OUTPUT, workflow=workflow, **DEFAULT_X_Y
    )
    output_node.parents.add(input_node)
    query = get_query_from_node(output_node)

    assert query.compile() == INPUT_QUERY


def test_select_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
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


def test_join_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
    second_input_node = input_node.make_clone()
    join_node = Node.objects.create(
        kind=Node.Kind.JOIN,
        workflow=workflow,
        **DEFAULT_X_Y,
        join_left="id",
        join_right="id",
    )
    join_node.parents.add(input_node, second_input_node)

    query = get_query_from_node(join_node)
    # Mocking the table conditionally requires a little bit more work
    # So we simply join the table with itself which leads to duplicate columns that
    # Are aliased
    join_query = "SELECT `id_left` AS `id`, `athlete_left`, `birthday_left`, `athlete_right`,\n       `birthday_right`\nFROM (\n  SELECT *\n  FROM (\n    SELECT `id` AS `id_left`, `athlete` AS `athlete_left`,\n           `birthday` AS `birthday_left`\n    FROM `gyana-1511894275181.dataset.table`\n  ) t1\n    INNER JOIN (\n      SELECT `id` AS `id_right`, `athlete` AS `athlete_right`,\n             `birthday` AS `birthday_right`\n      FROM `gyana-1511894275181.dataset.table`\n    ) t2\n      ON t1.`id_left` = t2.`id_right`\n) t0"
    assert query.compile() == join_query

    join_node.join_how = "outer"
    query = get_query_from_node(join_node)
    assert query.compile() == join_query.replace("INNER", "FULL OUTER")


def test_aggregation_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
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
    f"\nFROM (\n  SELECT *\n  FROM `{TABLE_NAME}`\n  UNION ALL"
    f"\n  SELECT *\n  FROM `{TABLE_NAME}`\n) t0"
)


def test_union_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
    second_input_node = input_node.make_clone()

    union_node = Node.objects.create(
        kind=Node.Kind.UNION,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    union_node.parents.add(input_node, second_input_node)

    assert get_query_from_node(union_node).compile() == UNION_QUERY

    union_node.union_distinct = True
    assert get_query_from_node(union_node).compile() == UNION_QUERY.replace(
        "UNION ALL", "UNION DISTINCT"
    )


def test_except_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
    second_input_node = input_node.make_clone()

    except_node = Node.objects.create(
        kind=Node.Kind.EXCEPT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    except_node.parents.add(input_node, second_input_node)

    assert get_query_from_node(except_node).compile() == UNION_QUERY.replace(
        "UNION ALL", "EXCEPT DISTINCT"
    )


def test_intersect_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)
    second_input_node = input_node.make_clone()

    intersect_node = Node.objects.create(
        kind=Node.Kind.INTERSECT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    intersect_node.parents.add(input_node, second_input_node)

    assert get_query_from_node(intersect_node).compile() == UNION_QUERY.replace(
        "UNION ALL", "INTERSECT DISTINCT"
    )


def test_sort_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)

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


def test_limit_node(logged_in_user, bigquery_client):
    input_node, workflow = setup_input_node(logged_in_user, bigquery_client)

    limit_node = Node.objects.create(
        kind=Node.Kind.LIMIT,
        workflow=workflow,
        **DEFAULT_X_Y,
    )
    limit_node.parents.add(input_node)

    limit_query = (
        f"SELECT `id`, `athlete`, `birthday`"
        f"\nFROM (\n  SELECT *\n  FROM `{TABLE_NAME}`"
        f"\n  LIMIT 100\n) t0"
    )
    assert get_query_from_node(limit_node).compile() == limit_query

    limit_node.limit_offset = 50
    limit_node.limit_limit = 250

    assert get_query_from_node(limit_node).compile() == limit_query.replace(
        "LIMIT 100", "LIMIT 250 OFFSET 50"
    )


def test_filter_node(logged_in_user, bigquery_client):
    assert False
