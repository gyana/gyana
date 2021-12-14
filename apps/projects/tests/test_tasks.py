from uuid import uuid4

import pytest
from celery_progress import backend
from django.utils import timezone

from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.projects.tasks import run_project_task
from apps.runs.models import GraphRun

pytestmark = pytest.mark.django_db


def test_run_project(
    project_factory,
    sheet_factory,
    integration_table_factory,
    workflow_table_factory,
    node_factory,
    mocker,
):
    mocker.patch("apps.sheets.tasks.run_sheet_sync_task")
    mocker.patch("apps.workflows.bigquery.run_workflow")

    project = project_factory()
    integration_table = integration_table_factory(
        project=project,
        integration__project=project,
        bq_table="integration_table",
        integration__kind=Integration.Kind.SHEET,
    )
    sheet = sheet_factory(integration=integration_table.integration)

    workflow_table = workflow_table_factory(
        project=project,
        workflow_node__workflow__project=project,
        bq_table="workflow_table",
    )
    input_node = node_factory(
        workflow=workflow_table.workflow_node.workflow,
        kind=Node.Kind.INPUT,
        input_table=integration_table,
    )

    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=GraphRun.State.RUNNING,
        started_at=timezone.now(),
    )

    run_project_task(graph_run.id)

    assert graph_run.runs.count() == 2
    assert graph_run.runs.filter(state=GraphRun.State.SUCCESS).count() == 2
    assert not graph_run.runs.exclude(state=GraphRun.State.SUCCESS).exists()
