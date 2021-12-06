from graphlib import TopologicalSorter

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


def run_workflows(project: Project):

    # Run all the workflows in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    workflows = Workflow.objects.filter(project=project).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            node.input_table.workflow_node.workflow
            for node in workflow.nodes.filter(
                kind=Node.Kind.INPUT, input_table__source=Table.Source.WORKFLOW_NODE
            )
            .select_related("input_table__workflow_node__workflow")
            .all()
        ]
        for workflow in workflows
    }

    ts = TopologicalSorter(graph)

    for workflow in ts.static_order():
        run_workflow(workflow)


def run_scheduled_workflows(project: Project):

    # Run all the scheduled workflows in a project. Designed to be idempotent,
    # i.e. this function is guaranteed to run each workflow no more than once
    # per day, and only after the parent entities are up to date.

    workflows = Workflow.objects.is_scheduled_in_project(project).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            node.input_table.source_obj
            for node in workflow.nodes.filter(kind=Node.Kind.INPUT)
            .select_related("input_table__workflow_node__workflow")
            .select_related("input_table__integration__sheet")
            .select_related("input_table__integration__connector")
            .all()
        ]
        for workflow in workflows
    }

    ts = TopologicalSorter(graph)

    for workflow in (e for e in ts.static_order() if isinstance(e, Workflow)):

        # Run a step when all the previous steps have run (even if they failed,
        # to keep it simple we don't propagate "blocked" information).

        parents = graph[workflow]

        for e in parents:
            e.refresh_from_db()

        scheduled_parents = [
            e for e in parents if hasattr(e, "is_scheduled") and e.is_scheduled
        ]

        if (
            workflow.is_scheduled
            and not workflow.up_to_date
            and all(e.up_to_date for e in scheduled_parents)
        ):
            run_workflow(workflow)
