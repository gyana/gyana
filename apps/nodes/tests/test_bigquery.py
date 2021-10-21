from unittest.mock import patch

import pytest
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
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
        [(column, type_.name) for column, type_ in TABLE.schema().items()],
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
