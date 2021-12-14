import json
from graphlib import CycleError, TopologicalSorter
from uuid import uuid4

from celery import shared_task
from celery_progress import backend
from django.utils import timezone

from apps.nodes.models import Node
from apps.runs.models import GraphRun, JobRun
from apps.sheets import tasks as sheet_tasks
from apps.sheets.models import Sheet
from apps.tables.models import Table
from apps.users.models import CustomUser
from apps.workflows import bigquery as workflow_tasks
from apps.workflows.models import Workflow

from .models import Project


def _update_progress_from_job_run(progress_recorder, run_info, job_run):
    run_info[job_run.source_obj.entity_id] = job_run.state
    progress_recorder.set_progress(0, 0, description=json.dumps(run_info))


def _get_entity_from_input_table(table: Table):
    if table.source == Table.Source.WORKFLOW_NODE:
        return table.workflow_node.workflow
    else:
        return table.integration.source_obj


@shared_task(bind=True)
def run_project_task(self, graph_run_id: int):

    progress_recorder = backend.ProgressRecorder(self)

    graph_run = GraphRun.objects.get(pk=graph_run_id)
    project = graph_run.project

    # Run all the workflows in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    workflows = project.workflow_set.all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            _get_entity_from_input_table(node.input_table)
            for node in workflow.nodes.filter(
                kind=Node.Kind.INPUT, input_table__isnull=False
            )
            .select_related("input_table__workflow_node__workflow")
            .select_related("input_table__integration__sheet")
            .select_related("input_table__integration__connector")
            .all()
        ]
        for workflow in workflows
    }

    graph.update(
        {
            sheet: []
            for sheet in Sheet.objects.filter(integration__project=project).all()
        }
    )

    job_runs = {
        entity: JobRun.objects.create(
            source=JobRun.Source.INTEGRATION
            if hasattr(entity, "integration")
            else JobRun.Source.WORKFLOW,
            integration=entity.integration if hasattr(entity, "integration") else None,
            workflow=entity if isinstance(entity, Workflow) else None,
            user=graph_run.user,
            graph_run=graph_run,
        )
        for entity in graph
    }

    run_info = {
        job_run.source_obj.entity_id: job_run.state for job_run in job_runs.values()
    }
    progress_recorder.set_progress(0, 0, description=json.dumps(run_info))

    ts = TopologicalSorter(graph)

    try:
        for entity in ts.static_order():

            job_run = job_runs[entity]
            job_run.state = JobRun.State.RUNNING
            job_run.started_at = timezone.now()
            _update_progress_from_job_run(progress_recorder, run_info, job_run)
            job_run.save()

            try:
                if isinstance(entity, Sheet):
                    sheet_tasks.run_sheet_sync_task(job_run.id, skip_up_to_date=True)
                elif isinstance(entity, Workflow):
                    workflow_tasks.run_workflow(job_run.id)
                job_run.state = JobRun.State.SUCCESS

            except Exception:
                job_run.state = JobRun.State.FAILED

            finally:
                _update_progress_from_job_run(progress_recorder, run_info, job_run)
                job_run.completed_at = timezone.now()
                job_run.save()

    except CycleError:
        Exception("Your integrations and workflows have a circular dependency")

    if graph_run.runs.filter(state=JobRun.State.FAILED).exists():
        raise Exception(
            "Not all of your integrations or workflows completed successfully"
        )


def run_project(project: Project, user: CustomUser):
    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=GraphRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_project_task.apply_async((graph_run.id,), task_id=graph_run.task_id)
    return graph_run
