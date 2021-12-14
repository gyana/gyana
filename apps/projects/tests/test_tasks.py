from uuid import uuid4

import pytest
from django.utils import timezone

from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.projects.tasks import run_project_task
from apps.runs.models import GraphRun
from apps.workflows.models import Workflow

pytestmark = pytest.mark.django_db


def test_run_project(
    project_factory,
    sheet_factory,
    integration_table_factory,
    workflow_table_factory,
    node_factory,
    mocker,
):
    run_sheet_sync_task = mocker.patch("apps.sheets.tasks.run_sheet_sync_task")
    run_workflow = mocker.patch("apps.workflows.bigquery.run_workflow")

    # integration -> workflow_1 -> workflow_2

    project = project_factory()
    integration_table = integration_table_factory(
        project=project,
        integration__project=project,
        bq_table="integration_table",
        integration__kind=Integration.Kind.SHEET,
    )
    integration = integration_table.integration
    sheet_factory(integration=integration)

    workflow_table_1 = workflow_table_factory(
        project=project,
        workflow_node__workflow__project=project,
        bq_table="workflow_table_1",
    )
    workflow_1 = workflow_table_1.workflow_node.workflow
    node_factory(
        workflow=workflow_1, kind=Node.Kind.INPUT, input_table=integration_table
    )

    workflow_table_2 = workflow_table_factory(
        project=project,
        workflow_node__workflow__project=project,
        bq_table="workflow_table_2",
    )
    workflow_2 = workflow_table_2.workflow_node.workflow
    node_factory(
        workflow=workflow_2, kind=Node.Kind.INPUT, input_table=workflow_table_1
    )

    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=GraphRun.State.RUNNING,
        started_at=timezone.now(),
    )

    run_project_task(graph_run.id)

    integration.refresh_from_db()
    workflow_1.refresh_from_db()
    workflow_2.refresh_from_db()

    # steps execute successfully

    assert integration.state == Integration.State.DONE
    assert workflow_1.state == Workflow.State.SUCCESS
    assert workflow_2.state == Workflow.State.SUCCESS

    assert run_sheet_sync_task.call_count == 1
    assert run_sheet_sync_task.call_args.args == (integration.latest_run.id,)

    assert run_workflow.call_count == 2
    assert run_workflow.call_args_list[0].args == (workflow_1.latest_run.id,)
    assert run_workflow.call_args_list[1].args == (workflow_2.latest_run.id,)

    assert graph_run.runs.count() == 3
    assert graph_run.runs.filter(state=GraphRun.State.SUCCESS).count() == 3
    assert not graph_run.runs.exclude(state=GraphRun.State.SUCCESS).exists()

    # dependency order is respected

    assert integration.latest_run.started_at < workflow_1.latest_run.started_at
    assert workflow_1.latest_run.started_at < workflow_2.latest_run.started_at
