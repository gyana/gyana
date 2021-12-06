import json
from graphlib import TopologicalSorter

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.base.errors import error_name_to_snake
from apps.nodes.bigquery import NodeResultNone, get_query_from_node
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.tables.models import Table
from apps.workflows.models import Workflow


def run_workflow(workflow: Workflow):
    output_nodes = workflow.nodes.filter(kind=Node.Kind.OUTPUT).all()
    client = clients.bigquery()

    for node in output_nodes:
        try:
            query = get_query_from_node(node)
        except NodeResultNone as err:
            node.error = error_name_to_snake(err)
            node.save()
            query = None
        if query is not None:

            with transaction.atomic():

                table, _ = Table.objects.get_or_create(
                    source=Table.Source.WORKFLOW_NODE,
                    bq_table=node.bq_output_table_id,
                    bq_dataset=workflow.project.team.tables_dataset_id,
                    project=workflow.project,
                    workflow_node=node,
                )

                client.query(
                    f"CREATE OR REPLACE TABLE {table.bq_id} as ({query.compile()})"
                ).result()

                table.data_updated = timezone.now()
                table.save()

    if workflow.failed:
        workflow.failed_at = timezone.now()
        workflow.save(update_fields=["failed_at"])

        return {node.id: node.error for node in workflow.nodes.all() if node.error}

    workflow.succeeded_at = timezone.now()
    workflow.last_run = timezone.now()
    # Use fields to not trigger auto_now on the updated field
    workflow.save(update_fields=["succeeded_at", "last_run"])


@shared_task(bind=True)
def run_workflows(self, project_id: int):

    progress_recorder = ProgressRecorder(self)

    run_info = {}

    project = Project.objects.get(pk=project_id)

    # Run all the workflows in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    workflows = Workflow.objects.filter(project=project).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: {
            node.input_table.workflow_node.workflow
            for node in workflow.nodes.filter(
                kind=Node.Kind.INPUT, input_table__source=Table.Source.WORKFLOW_NODE
            )
            .select_related("input_table__workflow_node__workflow")
            .all()
        }
        for workflow in workflows
    }

    ts = TopologicalSorter(graph)

    for workflow in ts.static_order():
        run_info[workflow.id] = "running"
        progress_recorder.set_progress(0, 0, description=json.dumps(run_info))
        run_workflow(workflow)
        run_info[workflow.id] = "done"
        progress_recorder.set_progress(0, 0, description=json.dumps(run_info))
