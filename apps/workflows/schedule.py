from graphlib import TopologicalSorter

from apps.nodes.models import Node
from apps.projects.models import Project
from apps.workflows.models import Workflow

from .bigquery import run_workflow


def run_scheduled_workflows(project: Project):

    # Run all the scheduled workflows in a project. Designed to be idempotent,
    # i.e. this function is guaranteed to run each workflow no more than once
    # per day, and only after the parent entities are up to date.

    workflows = Workflow.objects.is_scheduled_in_project(project).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: {
            node.input_table.source_obj
            for node in workflow.nodes.filter(kind=Node.Kind.INPUT)
            .select_related("input_table__workflow_node__workflow")
            .select_related("input_table__integration__sheet")
            .select_related("input_table__integration__connector")
            .all()
        }
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
            yield workflow.schedule_node_id, "running"
            run_workflow(workflow)
            yield workflow.schedule_node_id, "done"
