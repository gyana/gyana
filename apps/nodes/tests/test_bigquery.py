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

INPUT_QUERY = "SELECT *\nFROM `gyana-1511894275181.dataset.table`"
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
        "*", "count(*) as `count`"
    )

    aggregation_node.aggregations.create(column="id", function="sum")
    assert get_query_from_node(aggregation_node).compile() == INPUT_QUERY.replace(
        "*", "sum(`id`) as `id`"
    )

    aggregation_node.columns.create(column="birthday")
    assert (
        get_query_from_node(aggregation_node).compile()
        == INPUT_QUERY.replace("*", "sum(`id`) as `id`") + "/nGROUP BY `birthday"
    )
