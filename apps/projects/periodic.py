from graphlib import CycleError, TopologicalSorter

from celery import shared_task

from apps.base.tasks import honeybadger_check_in
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.sheets.models import Sheet
from apps.tables.models import Table

from .models import Project


def _get_entity_from_input_table(table: Table):
    if table.source == Table.Source.WORKFLOW_NODE:
        return table.workflow_node.workflow
    else:
        return table.integration.source_obj


@shared_task
def run_schedule_for_project(project_id: int):

    project = Project.objects.get(pk=project_id)

    project.update_schedule()

    # skip workflow if nothing to run
    if not project.periodic_task:
        return

    # Run all the workflows in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    workflows = project.workflow_set.filter(is_scheduled=True).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            _get_entity_from_input_table(node.input_table)
            for node in workflow.nodes.filter(
                kind=Node.Kind.INPUT, input_table__source=Table.Source.WORKFLOW_NODE
            )
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

    ts = TopologicalSorter(graph)

    try:
        for entity in ts.static_order():

            # Run a step when all the previous steps have run (even if they failed,
            # to keep it simple we don't propagate "blocked" information). This
            # is designed to be idempotent, we can keep running this task until
            # everything has completed successfully.

            if (
                hasattr(entity, "is_scheduled")
                and entity.is_scheduled
                and not entity.up_to_date
                and all(
                    e.up_to_date
                    for e in graph[entity]
                    if hasattr(e, "is_scheduled") and e.is_scheduled
                )
            ):
                entity.run_for_schedule()

    except CycleError:
        # todo: add an error to the schedule to track "is_circular"
        pass

    honeybadger_check_in("j6IrRd")
