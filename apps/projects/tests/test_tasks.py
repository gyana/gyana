from uuid import uuid4

import pytest
from django.utils import timezone

from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.projects import tasks
from apps.runs.models import GraphRun, JobRun
from apps.workflows.models import Workflow

pytestmark = pytest.mark.django_db


def test_run_project(
    project_factory,
    sheet_factory,
    connector_factory,
    integration_table_factory,
    workflow_table_factory,
    node_factory,
    mocker,
):
    run_sheet_sync_task = mocker.patch("apps.sheets.tasks.run_sheet_sync_task")
    run_workflow_task = mocker.patch("apps.workflows.tasks.run_workflow_task")

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
    # will be ignored by current implementation
    connector_factory(integration__project=project)

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

    tasks.run_project_task(graph_run.id)

    integration.refresh_from_db()
    workflow_1.refresh_from_db()
    workflow_2.refresh_from_db()

    # steps execute successfully

    assert integration.state == Integration.State.DONE
    assert workflow_1.state == Workflow.State.SUCCESS
    assert workflow_2.state == Workflow.State.SUCCESS

    assert run_sheet_sync_task.call_count == 1
    assert run_sheet_sync_task.call_args.args == (integration.latest_run.id,)

    assert run_workflow_task.call_count == 2
    assert run_workflow_task.call_args_list[0].args == (workflow_1.latest_run.id,)
    assert run_workflow_task.call_args_list[1].args == (workflow_2.latest_run.id,)

    assert graph_run.runs.count() == 3
    assert graph_run.runs.filter(state=GraphRun.State.SUCCESS).count() == 3
    assert not graph_run.runs.exclude(state=GraphRun.State.SUCCESS).exists()

    # dependency order is respected

    assert integration.latest_run.started_at < workflow_1.latest_run.started_at
    assert workflow_1.latest_run.started_at < workflow_2.latest_run.started_at

    # an error is raised by workflow_1

    def side_effect(job_run_id):
        job_run = JobRun.objects.get(pk=job_run_id)
        if job_run.source == JobRun.Source.WORKFLOW and job_run.workflow == workflow_1:
            raise Exception

    run_workflow_task.side_effect = side_effect

    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=GraphRun.State.RUNNING,
        started_at=timezone.now(),
    )

    with pytest.raises(Exception):
        tasks.run_project_task(graph_run.id)

    workflow_1.refresh_from_db()
    assert workflow_1.state == Workflow.State.FAILED
