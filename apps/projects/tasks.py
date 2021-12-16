import json
from graphlib import CycleError, TopologicalSorter
from uuid import uuid4

from celery import shared_task
from celery_progress import backend
from django.db.models import Q
from django.utils import timezone

from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.runs.models import GraphRun, JobRun
from apps.sheets import tasks as sheet_tasks
from apps.tables.models import Table
from apps.users.models import CustomUser
from apps.workflows import tasks as workflow_tasks
from apps.workflows.models import Workflow

from .models import Project


def _update_progress_from_job_run(progress_recorder, run_info, job_run):
    run_info[job_run.source_obj.entity_id] = job_run.state
    progress_recorder.set_progress(0, 0, description=json.dumps(run_info))


def _get_entity_from_input_table(table: Table):
    if table.source == Table.Source.WORKFLOW_NODE:
        return table.workflow_node.workflow
    else:
        return table.integration


def _is_scheduled(entity):
    if isinstance(entity, Integration):
        return entity.sheet.is_scheduled
    return entity.is_scheduled


@shared_task(bind=True)
def run_project_task(self, graph_run_id: int, scheduled_only=False):

    progress_recorder = backend.ProgressRecorder(self)

    graph_run = GraphRun.objects.get(pk=graph_run_id)
    project = graph_run.project

    # Run all the workflows and sheets in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            _get_entity_from_input_table(node.input_table)
            for node in workflow.nodes.filter(
                kind=Node.Kind.INPUT,
            )
            .filter(
                Q(input_table__integration__kind=Integration.Kind.SHEET)
                | Q(input_table__source=Table.Source.WORKFLOW_NODE)
            )
            .select_related("input_table__workflow_node__workflow")
            .select_related("input_table__integration")
            .all()
        ]
        for workflow in project.workflow_set.all()
    }

    graph.update(
        {
            integration: []
            for integration in project.integration_set.filter(
                kind=Integration.Kind.SHEET
            ).all()
        }
    )

    if scheduled_only:
        graph = {
            entity: [parent for parent in parents if _is_scheduled(parent)]
            for entity, parents in graph.items()
            if _is_scheduled(entity)
        }

    job_runs = {
        entity: JobRun.objects.create(
            source=JobRun.Source.INTEGRATION
            if isinstance(entity, Integration)
            else JobRun.Source.WORKFLOW,
            integration=entity if isinstance(entity, Integration) else None,
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
                if isinstance(entity, Integration):
                    sheet_tasks.run_sheet_sync_task(job_run.id, skip_up_to_date=True)
                elif isinstance(entity, Workflow):
                    workflow_tasks.run_workflow_task(job_run.id)
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
    run_project_task.apply_async((graph_run.id,), task_id=str(graph_run.task_id))
    return graph_run
