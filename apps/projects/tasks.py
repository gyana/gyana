import json
from graphlib import CycleError, TopologicalSorter
from uuid import uuid4

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.utils import timezone

from apps.nodes.models import Node
from apps.runs.models import GraphRun, JobRun
from apps.sheets.models import Sheet
from apps.sheets.tasks import run_sheet_sync_task
from apps.tables.models import Table
from apps.users.models import CustomUser
from apps.workflows.bigquery import run_workflow
from apps.workflows.models import Workflow

from .models import Project


def _update_progress_from_job_run(progress_recorder, run_info, job_run):
    run_info[job_run.source_obj.schedule_node_id] = job_run.state
    progress_recorder.set_progress(0, 0, description=json.dumps(run_info))


def _get_entity_from_input_table(table: Table):
    if table.source == Table.Source.WORKFLOW_NODE:
        return table.workflow_node.workflow
    else:
        return table.integration.source_obj


@shared_task(bind=True)
def run_project_task(self, graph_run_id: int):

    progress_recorder = ProgressRecorder(self)
    run_info = {}

    graph_run = GraphRun.objects.get(pk=graph_run_id)
    project = graph_run.project

    project.update_schedule()

    # skip workflow if nothing to run
    if project.periodic_task is None:
        return

    # Run all the workflows in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    workflows = Workflow.objects.is_scheduled_in_project(project).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            _get_entity_from_input_table(node.input_table)
            for node in workflow.nodes.filter(kind=Node.Kind.INPUT)
            .select_related("input_table__workflow_node__workflow")
            .select_related("input_table__integration__sheet")
            .select_related("input_table__integration__connector")
            .all()
        ]
        for workflow in workflows
    }

    graph.update(
        {sheet: [] for sheet in Sheet.objects.is_scheduled_in_project(project).all()}
    )

    job_runs = {
        entity: JobRun.objects.create(
            source=JobRun.Source.INTEGRATION
            if hasattr(entity, "integration")
            else JobRun.Source.WORKFLOW,
            integration=entity.integration if hasattr(entity, "integration") else None,
            workflow=entity if isinstance(entity, Workflow) else None,
            started_at=timezone.now(),
            user=graph_run.user,
            graph_run=graph_run,
        )
        for entity in graph
    }

    ts = TopologicalSorter(graph)

    try:
        for entity in ts.static_order():

            job_run = job_runs[entity]
            job_run.state = JobRun.State.RUNNING
            _update_progress_from_job_run(progress_recorder, run_info, job_run)
            job_run.save()

            try:
                if isinstance(entity, Sheet):
                    run_sheet_sync_task(job_run.id, skip_up_to_date=True)
                elif isinstance(entity, Workflow):
                    run_workflow(job_run.id)
                job_run.state = JobRun.State.SUCCESS

            except Exception:
                job_run.state = JobRun.State.FAILED

            finally:
                _update_progress_from_job_run(progress_recorder, run_info, job_run)
                job_run.completed_at = timezone.now()
                job_run.save()

    except CycleError:
        # todo: add an error to the schedule to track "is_circular"
        pass


def run_project(project: Project, user: CustomUser):
    graph_run = GraphRun.objects.create(
        project=project,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_project_task.apply_async((graph_run.id,), task_id=graph_run.task_id)
